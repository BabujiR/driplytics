"""P0-05: object-storage paths (fsspec URLs) and progress reporting."""

import json

import pandas as pd
import pytest

from driplytics_engine import ImportProgress, import_historian_export, import_large_file, storage
from driplytics_engine.readers import ExportLayout, estimate_input_rows


# ---------------------------------------------------------------- storage helpers
@pytest.mark.parametrize(
    "path,expected",
    [
        ("s3://bucket/key.csv", True),
        ("gs://bucket/key.csv", True),
        ("memory://x/y.csv", True),
        ("C:\\data\\export.csv", False),
        ("/tmp/export.csv", False),
    ],
)
def test_is_url(path, expected):
    assert storage.is_url(path) is expected


def test_suffix_and_join():
    assert storage.suffix("s3://b/dir/file.PARQUET") == ".parquet"
    assert storage.suffix("C:\\dir\\file.csv") == ".csv"
    assert storage.join("s3://b/out/", "values", "x") == "s3://b/out/values/x"


def test_estimate_rows_close_to_actual(data_dir, expected):
    est = estimate_input_rows(data_dir / "historian_long.csv")
    assert est == expected["long"]["total_values"]  # small file: sampled whole, exact


# ---------------------------------------------------------------- progress
def test_progress_events_in_memory(data_dir, mapping):
    events: list[ImportProgress] = []
    r = import_historian_export(data_dir / "historian_long.csv", mapping, progress=events.append)
    assert [e.stage for e in events] == ["reading", "processing", "done"]
    assert events[-1].fraction == 1.0 and events[-1].rows_done == r.report.total_values


def test_progress_events_large_file(tmp_path, data_dir, mapping, expected):
    events: list[ImportProgress] = []
    import_large_file(
        data_dir / "historian_long.csv", mapping, tmp_path, chunksize=700, progress=events.append
    )
    stages = [e.stage for e in events]
    assert stages[0] == "reading" and stages[-1] == "done" and "processing" in stages
    reading = [e for e in events if e.stage == "reading" and e.rows_done]
    assert len(reading) == -(-expected["long"]["total_values"] // 700)  # one update per chunk
    fractions = [e.fraction for e in events if e.fraction is not None]
    assert fractions == sorted(fractions) and fractions[-1] == 1.0  # monotonic, ends at 100 %
    processing = [e for e in events if e.stage == "processing"]
    assert processing[-1].tags_done == processing[-1].tags_total == 6


def test_progress_counts_file_rows_for_wide_files(tmp_path, data_dir, mapping):
    events: list[ImportProgress] = []
    import_large_file(
        data_dir / "historian_wide.csv",
        mapping,
        tmp_path,
        ExportLayout(quality_suffix=" Quality"),
        chunksize=200,
        progress=events.append,
    )
    rows = len(pd.read_csv(data_dir / "historian_wide.csv"))
    assert events[-1].rows_done == rows  # rows, not melted values


def test_failing_progress_callback_does_not_break_import(data_dir, mapping):
    def boom(_e: ImportProgress) -> None:
        raise RuntimeError("UI went away")

    r = import_historian_export(data_dir / "historian_long.csv", mapping, progress=boom)
    assert r.report.total_values == 5179


def test_fraction_math():
    assert ImportProgress("reading", 50, 100, 0, None, 1.0).fraction == pytest.approx(0.4)
    assert ImportProgress("reading", 10, None, 0, None, 1.0).fraction is None
    assert ImportProgress("processing", 100, 100, 3, 6, 1.0).fraction == pytest.approx(0.9)


# ---------------------------------------------------------------- object storage (fsspec memory://)
@pytest.fixture
def memfs():
    fsspec = pytest.importorskip("fsspec")
    fs = fsspec.filesystem("memory")
    fs.store.clear()
    yield fs
    fs.store.clear()


def test_import_from_object_storage_url(memfs, data_dir, mapping, expected):
    memfs.pipe("/bucket/raw/historian_long.csv", (data_dir / "historian_long.csv").read_bytes())
    r = import_historian_export("memory://bucket/raw/historian_long.csv", mapping)
    assert r.report.total_values == expected["long"]["total_values"]
    assert r.report.accepted == expected["long"]["accepted"]


def test_large_import_writes_to_object_storage(memfs, tmp_path, data_dir, mapping, expected):
    pytest.importorskip("pyarrow")
    memfs.pipe("/bucket/raw/historian_long.csv", (data_dir / "historian_long.csv").read_bytes())
    r = import_large_file(
        "memory://bucket/raw/historian_long.csv",
        mapping,
        "memory://bucket/clean/import-1",
        chunksize=1000,
        spill_dir=tmp_path,
    )
    assert r.report.accepted == expected["long"]["accepted"]
    files = memfs.ls("/bucket/clean/import-1/values", detail=False)
    assert len(files) == 6 and all(f.endswith(".parquet") for f in files)
    report = json.loads(memfs.cat("/bucket/clean/import-1/import_report.json"))
    assert report["total_values"] == expected["long"]["total_values"]
    assert list(tmp_path.iterdir()) == []  # local spill cleaned up
