"""P0-19: the synthetic Riverbend demo imports cleanly and carries the planted story."""

import pandas as pd
import pytest

from driplytics_engine import TagMapping, demo, import_historian_export


@pytest.fixture(scope="module")
def imported(tmp_path_factory):
    out = tmp_path_factory.mktemp("demo")
    export, mapping, truth = demo.write(out, days=30)
    result = import_historian_export(export, TagMapping.from_csv(mapping))
    return result, truth


def test_every_value_is_accounted_for_and_scoring_is_allowed(imported) -> None:
    result, truth = imported
    r = result.report
    assert r.total_values == truth.rows == 30 * 24 * 60 * 7 + 60 * 7  # + the repeated fall-back hour
    assert r.accepted + r.rejected + r.duplicates == r.total_values
    assert r.duplicates == 0
    assert r.rejected == truth.bad_quality_values
    assert {k for k, v in r.rejected_by_reason.items() if v} == {"bad_quality"}
    assert r.scoring_allowed and not r.unmapped_tags
    assert r.dst["ambiguous_first_pass"] > 0  # the window contains 2026-11-01


def test_totalizer_rolls_over(imported) -> None:
    result, _ = imported
    assert any(e["event"] == "rollover" for e in result.report.totalizer_events)


def test_leak_by_is_visible_in_the_clean_values(imported) -> None:
    result, truth = imported
    v = result.values
    flow = v[v["tag"] == "backwash_flow"].set_index("timestamp_utc")["value"]
    closed = v[v["tag"] == "fv101_closed"].set_index("timestamp_utc")["value"]
    both = pd.concat({"flow": flow, "closed": closed}, axis=1).dropna()
    shut = both[both["closed"] == 1.0]
    before = shut[shut.index < truth.leak_start_utc]["flow"]
    after = shut[shut.index >= truth.leak_start_utc]["flow"]
    assert before.median() < 0.5  # closed and tight
    assert 3.0 < after.median() < 5.5  # closed but passing about 4 gpm


def test_generation_is_deterministic() -> None:
    a, _ = demo.generate(days=2)
    b, _ = demo.generate(days=2)
    pd.testing.assert_frame_equal(a, b)
