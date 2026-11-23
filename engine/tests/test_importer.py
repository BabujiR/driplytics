import numpy as np
import pandas as pd
import pytest

from plant_ingest import ExportLayout, ImportConfig, TagMapping, import_historian_export, import_large_file
from plant_ingest.mapping import MappingError
from plant_ingest.report import ImportReport, UnbalancedLedgerError
from plant_ingest.totalizer import totalizer_to_rate


@pytest.fixture(scope="module")
def long_result(data_dir, mapping):
    return import_historian_export(data_dir / "historian_long.csv", mapping)


# ---------------------------------------------------------------- accounting
def test_counts_add_up_to_file_total(long_result, expected):
    r, e = long_result.report, expected["long"]
    assert r.accepted + r.rejected + r.duplicates == r.total_values == e["total_values"] == 5179
    assert (r.accepted, r.rejected, r.duplicates) == (e["accepted"], e["rejected"], e["duplicates"])


def test_every_planted_reason_is_counted(long_result, expected):
    got = {k: v for k, v in long_result.report.rejected_by_reason.items() if v}
    assert got == expected["long"]["rejected_by_reason"]


def test_ledger_has_one_outcome_per_input_value(long_result):
    led = long_result.ledger
    assert len(led) == long_result.report.total_values and led["seq"].is_unique
    counts = led["outcome"].value_counts().to_dict()
    assert counts == {"accepted": 5157, "rejected": 19, "duplicate": 3}
    assert (led.loc[led.outcome == "rejected", "reason"] != "").all()
    assert (led.loc[led.outcome != "rejected", "reason"] == "").all()


def test_report_refuses_to_build_when_unbalanced():
    with pytest.raises(UnbalancedLedgerError):
        ImportReport("x", "long", "UTC", 10, 5, 3, 1, {"empty_value": 3}, 0, {}, True, [], {}, [], 0, [])


def test_rejected_examples_in_report(long_result):
    ex = long_result.report.rejected_examples
    assert any(e["value"] == "I/O Timeout" for e in ex["bad_quality"])
    assert {e["timestamp"] for e in ex["unparseable_timestamp"]} == {"2026-11-31 00:00:00", "not-a-date"}


# ---------------------------------------------------------------- unmapped tags
def test_unmapped_tags_listed_and_block_scoring(long_result):
    r = long_result.report
    assert r.unmapped_tags == {"XV-999.PV": 3}
    assert r.scoring_allowed is False and "XV-999.PV" in r.scoring_blocked_reasons[0]


def test_fully_mapped_file_allows_scoring(data_dir, mapping):
    r = import_historian_export(data_dir / "leakby_historian.csv", mapping)
    assert r.report.scoring_allowed and r.report.rejected == 0


# ---------------------------------------------------------------- DST
def test_fall_back_hour_gives_continuous_utc_series(long_result, expected):
    v = long_result.values
    f = v[(v.tag == "inlet_flow") & (v.timestamp_utc >= pd.Timestamp("2026-11-01", tz="UTC"))]
    assert f.timestamp_utc.is_unique and f.timestamp_utc.is_monotonic_increasing
    steps = f.timestamp_utc.diff().dropna().dt.total_seconds()
    # 841 samples, 4 removed (empty, digital state, Bad flag, conflicting pair) -> four 20 s steps
    assert len(f) == expected["long"]["fall_samples_per_tag"] - 4
    assert steps.value_counts().to_dict() == {10.0: len(f) - 1 - 4, 20.0: 4}
    assert f.timestamp_utc.min() == pd.Timestamp("2026-11-01 04:50:00Z")
    assert f.timestamp_utc.max() == pd.Timestamp("2026-11-01 07:10:00Z")


def test_dst_stats_in_report(long_result):
    dst = long_result.report.dst
    assert dst["nonexistent_local_time"] == 3
    assert dst["ambiguous_first_pass"] > 0 and dst["ambiguous_second_pass"] > 0


def test_duplicate_inside_repeated_hour_is_duplicate_not_conflict(long_result):
    led = long_result.ledger
    assert (led.outcome == "duplicate").sum() == 3


# ---------------------------------------------------------------- units, states, totalizer
def test_unit_conversion_applied(long_result):
    v = long_result.values.groupby("tag", observed=True)
    assert v["value"].mean()["inlet_flow"] == pytest.approx(250 * 0.227124707, rel=0.01)
    assert v["value"].mean()["inlet_pressure"] == pytest.approx(55 * 6.894757, rel=0.01)
    assert v["value"].mean()["water_temp"] == pytest.approx((62 - 32) * 5 / 9, rel=0.01)
    units = long_result.values.drop_duplicates("tag").set_index("tag")["unit"].astype(str).to_dict()
    assert units["inlet_flow"] == "m3/h" and units["inlet_volume_rate"] == "gpm"


def test_state_tags_normalized_to_0_1(long_result):
    v = long_result.values
    for tag in ("pump_201_running", "fv101_closed"):
        assert set(v.loc[v.tag == tag, "value"].unique()) == {0.0, 1.0}


def test_totalizer_rate_through_rollover_reset_and_dst(long_result):
    v = long_result.values
    rate = v[v.tag == "inlet_volume_rate"]
    assert rate["derived"].all()
    assert rate["value"].to_numpy() == pytest.approx(250.0, abs=0.01)  # constant 250 gpm
    assert len(rate) == 841 - 2                                         # first sample + reset interval
    ev = {e["event"] for e in long_result.report.totalizer_events}
    assert ev == {"rollover", "reset"}


def test_totalizer_gap_gives_no_rate(mapping):
    spec = mapping["FQI-101.TOT"]
    ts = pd.Series(pd.to_datetime(["2026-01-01 00:00:00", "2026-01-01 00:00:10", "2026-01-01 01:00:00"], utc=True))
    out, _, gaps = totalizer_to_rate(ts, np.array([0, 41.6667, 9999]), pd.Series(["good"] * 3), spec)
    assert len(out) == 1 and gaps == 1


def test_uncertain_quality_kept_and_counted(long_result):
    assert long_result.report.accepted_uncertain == 1
    assert (long_result.values["quality"] == "uncertain").sum() == 1


# ---------------------------------------------------------------- wide format
def test_wide_format(data_dir, mapping, expected):
    r = import_historian_export(data_dir / "historian_wide.csv", mapping, ExportLayout(quality_suffix=" Quality"))
    e = expected["wide"]
    assert r.report.format == "wide"
    assert (r.report.total_values, r.report.accepted, r.report.rejected, r.report.duplicates) == \
           (e["total_values"], e["accepted"], e["rejected"], e["duplicates"])
    assert {k: v for k, v in r.report.rejected_by_reason.items() if v} == e["rejected_by_reason"]


def test_wide_blank_cells_can_be_ignored(data_dir, mapping):
    r = import_historian_export(data_dir / "historian_wide.csv", mapping,
                                ExportLayout(quality_suffix=" Quality", wide_blank_cells="ignore"))
    assert r.report.blank_cells_ignored == 3 and r.report.rejected_by_reason["empty_value"] == 0
    assert r.report.accepted + r.report.rejected + r.report.duplicates == r.report.total_values


# ---------------------------------------------------------------- mapping validation
def test_mapping_validation_errors():
    bad = pd.DataFrame([
        dict(raw_tag="A", canonical_tag="a", role="flow", source_unit="gpm", target_unit="psi"),
        dict(raw_tag="B", canonical_tag="b", role="valve_state"),
        dict(raw_tag="C", canonical_tag="c", role="flow", source_unit="gpm", target_unit="gpm", is_totalizer="true"),
    ])
    with pytest.raises(MappingError) as e:
        TagMapping.from_frame(bad)
    msg = str(e.value)
    assert "line 2" in msg and "line 3" in msg and "line 4" in msg


# ---------------------------------------------------------------- large-file path
def test_large_path_matches_in_memory(tmp_path, data_dir, mapping, long_result):
    big = import_large_file(data_dir / "historian_long.csv", mapping, tmp_path, chunksize=700)
    a, b = big.report, long_result.report
    assert (a.total_values, a.accepted, a.rejected, a.duplicates) == (b.total_values, b.accepted, b.rejected, b.duplicates)
    assert a.rejected_by_reason == b.rejected_by_reason and a.dst == b.dst
    files = sorted((tmp_path / "values").iterdir())
    vals = pd.concat([pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_pickle(f) for f in files])
    vals = vals.sort_values(["tag", "timestamp_utc"]).reset_index(drop=True)
    mem = long_result.values.sort_values(["tag", "timestamp_utc"]).reset_index(drop=True)
    assert len(vals) == len(mem)
    np.testing.assert_allclose(vals["value"].to_numpy(), mem["value"].to_numpy())
    assert (tmp_path / "import_report.json").exists()


# ---------------------------------------------------------------- parquet
def test_parquet_long_input(tmp_path, data_dir, mapping, long_result):
    pytest.importorskip("pyarrow")
    df = pd.read_csv(data_dir / "historian_long.csv", dtype=str, keep_default_na=False)
    p = tmp_path / "long.parquet"
    df.to_parquet(p, index=False)
    r = import_historian_export(p, mapping)
    assert r.report.rejected_by_reason == long_result.report.rejected_by_reason
    assert r.report.accepted == long_result.report.accepted
