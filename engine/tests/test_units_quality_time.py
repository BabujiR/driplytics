import numpy as np
import pandas as pd
import pytest

from plant_ingest.constants import Quality
from plant_ingest.quality import is_digital_state, normalize_quality
from plant_ingest.timeconv import localize_to_utc, parse_timestamps
from plant_ingest.units import UnitError, convert


# ---------------------------------------------------------------- units
@pytest.mark.parametrize("v,src,dst,want", [
    (100, "gpm", "m3/h", 22.7124707),
    (1, "MGD", "gpm", 694.444),
    (212, "degF", "degC", 100.0),
    (0, "degC", "K", 273.15),
    (14.5038, "psi", "bar", 1.0),
    (1, "kgal", "gal", 1000.0),
])
def test_convert(v, src, dst, want):
    assert convert(v, src, dst) == pytest.approx(want, rel=1e-4)


def test_convert_rejects_wrong_dimension():
    with pytest.raises(UnitError):
        convert(1, "gpm", "psi")


def test_convert_keeps_series_index():
    s = pd.Series([0.0, 100.0], index=[5, 6])
    out = convert(s, "degC", "degF")
    assert list(out.index) == [5, 6] and out.iloc[1] == pytest.approx(212)


# ---------------------------------------------------------------- quality
def test_quality_text_and_opc():
    raw = pd.Series(["Good", "suspect", "BAD", "192", "64", "0", "", "weird"])
    q = normalize_quality(raw, len(raw)).astype(str).tolist()
    assert q == ["good", "uncertain", "bad", "good", "uncertain", "bad", "good", "bad"]


def test_quality_blank_default_is_configurable():
    q = normalize_quality(pd.Series(["", ""]), 2, blank=Quality.UNCERTAIN)
    assert set(q.astype(str)) == {"uncertain"}


def test_quality_numeric_column():
    q = normalize_quality(pd.Series([192, 0, 68]), 3).astype(str).tolist()
    assert q == ["good", "bad", "uncertain"]


def test_digital_states():
    s = pd.Series(["I/O Timeout", " bad input ", "12.5", "Comm Fail", "RUNNING"])
    assert is_digital_state(s).tolist() == [True, True, False, True, False]


# ---------------------------------------------------------------- time / DST
def test_fall_back_hour_resolved_by_file_order():
    local = parse_timestamps(pd.Series(
        ["2026-11-01 01:59:50", "2026-11-01 01:00:00", "2026-11-01 01:00:10"]))
    utc, nonexist, st = localize_to_utc(local, pd.Series(["A"] * 3), "America/New_York")
    assert [t.strftime("%H:%M:%S") for t in utc] == ["05:59:50", "06:00:00", "06:00:10"]
    assert not nonexist.any() and st.ambiguous_second_pass == 2


def test_fall_back_per_tag_interleaved():
    # two tags interleaved; only the order within each tag matters
    ts = ["01:59:50", "01:59:50", "01:00:00", "01:00:00"]
    local = parse_timestamps(pd.Series([f"2026-11-01 {t}" for t in ts]))
    utc, _, _ = localize_to_utc(local, pd.Series(["A", "B", "A", "B"]), "America/New_York")
    assert utc.dt.strftime("%H:%M:%S").tolist() == ["05:59:50", "05:59:50", "06:00:00", "06:00:00"]


def test_exact_repeat_without_jump_stays_first_pass():
    local = parse_timestamps(pd.Series(["2026-11-01 01:30:00", "2026-11-01 01:30:00"]))
    utc, _, _ = localize_to_utc(local, pd.Series(["A", "A"]), "America/New_York")
    assert utc.iloc[0] == utc.iloc[1]  # becomes a duplicate later, not a fake hour


def test_spring_forward_gap_is_nonexistent():
    local = parse_timestamps(pd.Series(["2026-03-08 01:59:50", "2026-03-08 02:30:00", "2026-03-08 03:00:00"]))
    utc, nonexist, _ = localize_to_utc(local, None, "America/New_York")
    assert nonexist.tolist() == [False, True, False]
    assert (utc.iloc[2] - utc.iloc[0]) == pd.Timedelta(seconds=10)


def test_offset_timestamps_need_no_guessing():
    local = parse_timestamps(pd.Series(["2026-11-01T01:30:00-04:00", "2026-11-01T01:30:00-05:00"]))
    utc, _, _ = localize_to_utc(local, None, "America/New_York")
    assert (utc.iloc[1] - utc.iloc[0]) == pd.Timedelta(hours=1)


def test_explicit_timestamp_format_and_bad_values():
    out = parse_timestamps(pd.Series(["11/01/2026 01:30:00 PM", "garbage"]), "%m/%d/%Y %I:%M:%S %p")
    assert out.iloc[0] == pd.Timestamp("2026-11-01 13:30:00") and pd.isna(out.iloc[1])


def test_utc_export_passthrough():
    local = parse_timestamps(pd.Series(["2026-11-01 01:30:00"]))
    utc, nonexist, _ = localize_to_utc(local, None, "UTC")
    assert utc.iloc[0] == pd.Timestamp("2026-11-01 01:30:00Z") and not nonexist.any()
