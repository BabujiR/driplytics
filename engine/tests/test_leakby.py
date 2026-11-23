import pandas as pd
import pytest

from driplytics_engine import import_historian_export
from driplytics_engine.clampon import ClampOnLayout, load_clampon_export
from driplytics_engine.leakby import LeakByConfig, run_leak_by_check
from driplytics_engine.states import state_on_grid

LAYOUT = ClampOnLayout(
    timestamp_col="Date/Time",
    upstream_flow_col="CH1 Volume Flow",
    upstream_quality_col="CH1 Signal Quality",
    downstream_flow_col="CH2 Volume Flow",
    downstream_quality_col="CH2 Signal Quality",
    skiprows=3,
)


def cfg(**kw):
    base = dict(
        valve_state_tag="fv101_closed",
        pump_state_tag="pump_201_running",
        valve_label="FV-101",
        pump_label="P-201",
        low_flow_cutoff=1.0,
        min_signal_quality=60,
    )
    return LeakByConfig(**{**base, **kw})


@pytest.fixture(scope="module")
def hist(data_dir, mapping):
    return import_historian_export(data_dir / "leakby_historian.csv", mapping)


@pytest.fixture(scope="module")
def clamp(data_dir, expected):
    return load_clampon_export(
        data_dir / "clampon_export.csv", LAYOUT, clock_offset_s=expected["leakby"]["clock_offset_s"]
    )


# ---------------------------------------------------------------- clamp-on import
def test_clampon_rows_accounted(clamp, expected):
    r = clamp.report
    assert r["rows"] == expected["leakby"]["rows"]
    assert r["rejected"]["unparseable_timestamp"] == 2
    assert r["non_numeric_cells"]["down_flow"] == 1


def test_clampon_aligned_to_historian_grid(clamp):
    idx = clamp.data.index
    assert idx.min() == pd.Timestamp("2026-11-10 15:00:00Z")  # clock offset removed
    assert (idx.second % 10 == 0).all() and idx.is_unique
    assert clamp.data["n_samples"].median() == 10  # 1 s samples per 10 s point


def test_without_clock_offset_timeline_is_shifted(data_dir):
    raw = load_clampon_export(data_dir / "clampon_export.csv", LAYOUT, clock_offset_s=0)
    assert raw.data.index.min() == pd.Timestamp("2026-11-10 15:00:50Z")


# ---------------------------------------------------------------- state join
def test_state_on_grid_staleness_and_settling(hist):
    grid = pd.date_range("2026-11-10 15:09:50Z", periods=4, freq="60s")
    st = state_on_grid(hist.values, "fv101_closed", grid, max_age="15min", settling="120s")
    assert st["state"].tolist() == [0.0, 1.0, 1.0, 1.0]
    assert st["in_transition"].tolist() == [False, True, True, False]
    late = state_on_grid(
        hist.values, "fv101_closed", pd.DatetimeIndex([pd.Timestamp("2026-11-10 18:00Z")]), max_age="15min"
    )
    assert late["state"].isna().all()


# ---------------------------------------------------------------- the check
def test_flags_both_planted_events(clamp, hist, expected):
    r = run_leak_by_check(clamp, hist.values, cfg(), hist.report)
    assert r.status == "FLAGGED" and len(r.events) == 2
    e1, e2 = r.events.iloc[0], r.events.iloc[1]
    x1 = expected["leakby"]["event1"]
    assert e1.start_utc == pd.Timestamp(x1["start_utc"]) and e1.end_utc == pd.Timestamp(x1["end_utc"])
    assert e1.duration_min == x1["duration_min"] and e1.condition == "valve_closed"
    assert e1.mean_flow == pytest.approx(4.0, abs=0.2)
    assert abs(e2.start_utc - pd.Timestamp(expected["leakby"]["event2"]["start_utc_approx"])) <= pd.Timedelta(
        "10s"
    )
    assert e2.condition == "pump_off"


def test_reason_is_plain_words(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(), hist.report)
    text = r.events.iloc[0].reason
    for piece in (
        "Downstream flow averaged",
        "low-flow cutoff of 1 gpm",
        "valve FV-101 reported CLOSED",
        "18.0 minutes",
        "leaking by",
    ):
        assert piece in text
    assert any("signal quality was below 60" in s for s in r.reasons)


def test_poor_signal_period_not_judged(clamp, hist):
    strict = run_leak_by_check(clamp, hist.values, cfg(), hist.report)
    loose = run_leak_by_check(clamp, hist.values, cfg(min_signal_quality=10), hist.report)
    assert strict.summary["minutes_excluded_poor_signal"] == pytest.approx(10, abs=0.2)
    assert (
        loose.events.iloc[0].end_utc > strict.events.iloc[0].end_utc
    )  # now runs into the poor-signal period


def test_flow_below_cutoff_is_clear(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(low_flow_cutoff=10), hist.report)
    assert r.status == "CLEAR" and r.events.empty and "stayed at or below" in r.reasons[0]


def test_short_bursts_not_flagged(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(min_duration="30min"), hist.report)
    assert r.status == "CLEAR" and "bursts shorter than 30min" in r.reasons[0]


def test_valve_only_check(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(pump_state_tag=None), hist.report)
    assert r.status == "FLAGGED" and list(r.events.condition) == ["valve_closed"]


# ---------------------------------------------------------------- skips
def test_missing_valve_tag_skips_with_reason(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(valve_state_tag="fv999_closed"), hist.report)
    assert r.status == "SKIPPED" and r.events.empty
    assert r.reasons == ["Required valve position tag 'fv999_closed' is missing from the historian data."]


def test_no_state_tags_configured_skips(clamp, hist):
    r = run_leak_by_check(clamp, hist.values, cfg(valve_state_tag=None, pump_state_tag=None))
    assert r.status == "SKIPPED" and "nothing to compare" in r.reasons[0]


def test_blocked_import_skips(clamp, data_dir, mapping):
    blocked = import_historian_export(data_dir / "historian_long.csv", mapping)
    r = run_leak_by_check(clamp, blocked.values, cfg(), blocked.report)
    assert r.status == "SKIPPED" and "unmapped" in r.reasons[0]


def test_missing_signal_quality_skips(data_dir, hist):
    lay = ClampOnLayout(**{**LAYOUT.__dict__, "downstream_quality_col": "not-there"})
    c = load_clampon_export(data_dir / "clampon_export.csv", lay, clock_offset_s=45)
    r = run_leak_by_check(c, hist.values, cfg(), hist.report)
    assert r.status == "SKIPPED" and "signal-quality" in r.reasons[0]


def test_state_data_outside_window_skips(clamp, hist):
    shifted = hist.values.assign(timestamp_utc=hist.values.timestamp_utc - pd.Timedelta("2D"))
    r = run_leak_by_check(clamp, shifted, cfg(), hist.report)
    assert r.status == "SKIPPED" and "no samples within" in r.reasons[0]
