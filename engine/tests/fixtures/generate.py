"""Generate the synthetic test fixtures (deterministic, seed 42). All data is made up.

    python tests/fixtures/generate.py            # writes into tests/fixtures/data/

Files and what is planted in them (exact expected counts go to expected.json):

tag_mapping.csv          6 mapped tags (flow, totalizer, pressure, temperature, pump, valve)
historian_long.csv       Long format, America/New_York local time, 10 s sampling.
                         * fall-back day 2026-11-01 00:50 EDT .. 02:10 EST (the 01:xx hour appears twice)
                         * spring-forward day 2026-03-08 01:50 EST .. 03:10 EDT for one tag,
                           plus 3 planted rows inside the missing 02:xx hour
                         * totalizer that rolls over at 1,000,000 gal and is reset to 0 once
                         * planted bad rows: unparseable timestamps, unmapped tag, empty values,
                           PI digital states, non-numeric text, Bad / OPC-0 quality, an unknown
                           valve state, exact duplicates (one inside the repeated hour) and a
                           conflicting duplicate pair
historian_wide.csv       Wide format with a per-tag quality column, an unmapped column, blank
                         cells, a digital state and a fully duplicated row
leakby_historian.csv     Pump and valve states for the leak-by scenario (2026-11-10)
clampon_export.csv       1 s two-channel clamp-on export, meter clock 45 s FAST, metadata header,
                         a signal-loss period, garbage rows
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

TZ = "America/New_York"
OUT = Path(__file__).parent / "data"
RATE_GPM = 250.0
GAL_PER_STEP = RATE_GPM / 6.0          # 10 s at 250 gpm


def _local(ts_utc: pd.Timestamp) -> str:
    return ts_utc.tz_convert(TZ).strftime("%Y-%m-%d %H:%M:%S")


def write_mapping(out: Path) -> None:
    pd.DataFrame([
        dict(raw_tag="FIT-101.PV", canonical_tag="inlet_flow", role="flow", source_unit="gpm",
             target_unit="m3/h", is_totalizer="false", low_flow_cutoff="0.23"),
        dict(raw_tag="FQI-101.TOT", canonical_tag="inlet_volume_rate", role="flow", source_unit="gal",
             target_unit="gpm", is_totalizer="true", rollover_max="1000000", max_gap_s="300"),
        dict(raw_tag="PIT-101.PV", canonical_tag="inlet_pressure", role="pressure", source_unit="psi",
             target_unit="kPa"),
        dict(raw_tag="TT-101.PV", canonical_tag="water_temp", role="temperature", source_unit="degF",
             target_unit="degC"),
        dict(raw_tag="P-201.RUN", canonical_tag="pump_201_running", role="pump_state",
             state_true="RUNNING", state_false="STOPPED"),
        dict(raw_tag="FV-101.ZSC", canonical_tag="fv101_closed", role="valve_state",
             state_true="1", state_false="0"),
    ]).to_csv(out / "tag_mapping.csv", index=False)


def write_long(out: Path, rng: np.random.Generator) -> dict:
    exp = {"rejected_by_reason": {}, "duplicates": 0}

    def plant(reason: str, n: int = 1) -> None:
        exp["rejected_by_reason"][reason] = exp["rejected_by_reason"].get(reason, 0) + n

    rows: list[dict] = []
    # spring-forward segment: one tag, real samples on both sides of the gap
    for t in pd.date_range("2026-03-08 06:50:00Z", "2026-03-08 07:10:00Z", freq="10s"):
        rows.append(dict(ts=_local(t), tag="FIT-101.PV", value=f"{240 + rng.normal(0, 1):.3f}", quality="Good"))
        if t == pd.Timestamp("2026-03-08 06:59:50Z"):     # 01:59:50 EST, next real sample is 03:00:00 EDT
            for wall in ("02:15:00", "02:30:00", "02:45:00"):  # times that do not exist that night
                rows.append(dict(ts=f"2026-03-08 {wall}", tag="FIT-101.PV", value="241.0", quality="Good"))
                plant("nonexistent_local_time")

    # fall-back segment: all tags, time-major (interleaved) like a PI "multi-tag" export
    times = pd.date_range("2026-11-01 04:50:00Z", "2026-11-01 07:10:00Z", freq="10s")
    for k, t in enumerate(times):
        tot = (999_000 + k * GAL_PER_STEP) % 1_000_000 if t < pd.Timestamp("2026-11-01 06:30:00Z") \
            else (t - pd.Timestamp("2026-11-01 06:30:00Z")).total_seconds() / 10 * GAL_PER_STEP
        valve = "1" if (k // 120) % 2 else ("0" if k % 7 else "0.0")
        pump = "RUNNING" if k < 600 else ("Stopped" if k % 2 else "STOPPED")
        for tag, val in (("FIT-101.PV", f"{RATE_GPM + rng.normal(0, 2):.3f}"),
                         ("FQI-101.TOT", f"{tot:.4f}"),
                         ("PIT-101.PV", f"{55 + rng.normal(0, 0.5):.3f}"),
                         ("TT-101.PV", f"{62 + rng.normal(0, 0.2):.3f}"),
                         ("P-201.RUN", pump),
                         ("FV-101.ZSC", valve)):
            rows.append(dict(ts=_local(t), tag=tag, value=val, quality="Good", _utc=t))

    def find(tag: str, utc: str) -> int:
        u = pd.Timestamp(utc)
        return next(i for i, r in enumerate(rows) if r.get("_utc") == u and r["tag"] == tag)

    # replacements (row count unchanged)
    rows[find("FIT-101.PV", "2026-11-01 05:00:00Z")]["value"] = "";               plant("empty_value")
    rows[find("PIT-101.PV", "2026-11-01 05:00:00Z")]["value"] = "   ";            plant("empty_value")
    rows[find("TT-101.PV", "2026-11-01 05:10:00Z")]["value"] = "I/O Timeout";     plant("bad_quality")
    r = rows[find("FIT-101.PV", "2026-11-01 05:10:10Z")]
    r["value"], r["quality"] = "Bad Input", "Bad";                                plant("bad_quality")
    rows[find("PIT-101.PV", "2026-11-01 05:20:00Z")]["value"] = "12..5";          plant("non_numeric_value")
    rows[find("TT-101.PV", "2026-11-01 05:20:00Z")]["value"] = "abc";             plant("non_numeric_value")
    rows[find("FIT-101.PV", "2026-11-01 05:30:00Z")]["quality"] = "Bad";          plant("bad_quality")
    rows[find("PIT-101.PV", "2026-11-01 05:30:00Z")]["quality"] = "0";            plant("bad_quality")  # OPC bad
    rows[find("FIT-101.PV", "2026-11-01 05:40:00Z")]["quality"] = "Suspect"       # accepted, uncertain
    rows[find("FV-101.ZSC", "2026-11-01 05:50:00Z")]["value"] = "TRAVEL";         plant("unrecognized_state")

    # insertions (work from the end so earlier indexes stay valid)
    inserts = []
    for tag, utc in (("FIT-101.PV", "2026-11-01 06:00:00Z"),   # 01:00:00 EST - inside the repeated hour
                     ("PIT-101.PV", "2026-11-01 05:45:00Z"),
                     ("P-201.RUN", "2026-11-01 05:45:00Z")):
        i = find(tag, utc)
        inserts.append((i + 1, dict(rows[i])))
        exp["duplicates"] += 1
    i = find("FIT-101.PV", "2026-11-01 05:55:00Z")
    inserts.append((i + 1, dict(rows[i], value="999.0")))
    plant("conflicting_duplicate", 2)                            # both copies rejected
    for i, row in sorted(inserts, key=lambda x: -x[0]):
        rows.insert(i, row)

    rows.insert(10, dict(ts="2026-11-31 00:00:00", tag="FIT-101.PV", value="1", quality="Good"))
    rows.insert(20, dict(ts="not-a-date", tag="FIT-101.PV", value="1", quality="Good"))
    plant("unparseable_timestamp", 2)
    for j, utc in enumerate(("05:00:00", "05:00:10", "05:00:20")):
        rows.insert(find("FIT-101.PV", f"2026-11-01 {utc}Z") + 1,
                    dict(ts=_local(pd.Timestamp(f"2026-11-01 {utc}Z")), tag="XV-999.PV", value="7", quality="Good"))
    plant("unmapped_tag", 3)

    df = pd.DataFrame(rows)[["ts", "tag", "value", "quality"]].rename(columns={"ts": "timestamp"})
    df.to_csv(out / "historian_long.csv", index=False)

    exp["total_values"] = len(df)
    exp["rejected"] = sum(exp["rejected_by_reason"].values())
    exp["accepted"] = exp["total_values"] - exp["rejected"] - exp["duplicates"]
    exp["unmapped_tags"] = ["XV-999.PV"]
    exp["accepted_uncertain"] = 1
    exp["fall_samples_per_tag"] = len(times)
    exp["totalizer_events"] = {"rollover": 1, "reset": 1}
    return exp


def write_wide(out: Path, rng: np.random.Generator) -> dict:
    times = pd.date_range("2026-11-01 04:50:00Z", "2026-11-01 07:10:00Z", freq="10s")
    df = pd.DataFrame({
        "timestamp": [_local(t) for t in times],
        "FIT-101.PV": [f"{RATE_GPM + rng.normal(0, 2):.3f}" for _ in times],
        "FIT-101.PV Quality": "Good",
        "PIT-101.PV": [f"{55 + rng.normal(0, 0.5):.3f}" for _ in times],
        "P-201.RUN": "RUNNING",
        "XV-999.PV": "7",
    })
    df.loc[[100, 200, 300], "PIT-101.PV"] = ""            # 3 blank cells
    df.loc[400, "FIT-101.PV"] = "Comm Fail"               # PI digital state
    df.loc[500, "FIT-101.PV Quality"] = "Bad"             # quality column says bad
    df = pd.concat([df.iloc[:601], df.iloc[[600]], df.iloc[601:]], ignore_index=True)  # duplicated row
    df.to_csv(out / "historian_wide.csv", index=False)
    tag_cols = 4
    total = len(df) * tag_cols
    rej = {"unmapped_tag": len(df), "empty_value": 3, "bad_quality": 2}
    dups = tag_cols - 1                                   # the unmapped cell of that row is rejected instead
    return {"total_values": total, "rejected_by_reason": rej, "rejected": sum(rej.values()),
            "duplicates": dups, "accepted": total - sum(rej.values()) - dups,
            "unmapped_tags": ["XV-999.PV"]}


def write_leakby(out: Path, rng: np.random.Generator) -> dict:
    """2026-11-10 (EST, UTC-5). True local timeline:
        10:00-10:10 valve open, pump running, ~300 gpm
        10:10       valve closes (limit switch), flow decays to ~4 gpm over 60 s
        10:10-10:30 valve closed, ~4 gpm downstream, good signal          -> LEAK-BY event
        10:30-10:40 valve closed, ~4 gpm but signal quality ~25 %          -> not judged
        10:40       valve opens, pump stops
        10:40-10:50 pump off, ~0.3 gpm (below 1.0 gpm cutoff)              -> fine
        10:50-11:00 pump off, ~6 gpm                                       -> pump-off flow event
    """
    hist = []
    for t in pd.date_range("2026-11-10 14:50:00Z", "2026-11-10 16:10:00Z", freq="10s"):
        loc = t.tz_convert(TZ)
        closed = "1" if pd.Timestamp("2026-11-10 15:10:00Z") <= t < pd.Timestamp("2026-11-10 15:40:00Z") else "0"
        running = "RUNNING" if t < pd.Timestamp("2026-11-10 15:40:00Z") else "STOPPED"
        hist += [dict(timestamp=loc.strftime("%Y-%m-%d %H:%M:%S"), tag="FV-101.ZSC", value=closed, quality="Good"),
                 dict(timestamp=loc.strftime("%Y-%m-%d %H:%M:%S"), tag="P-201.RUN", value=running, quality="Good")]
    pd.DataFrame(hist).to_csv(out / "leakby_historian.csv", index=False)

    offset = 45  # meter clock is 45 s fast
    true_t = pd.date_range("2026-11-10 15:00:00Z", "2026-11-10 15:59:59Z", freq="1s")
    m = ((true_t - true_t[0]).total_seconds() / 60).to_numpy()  # minutes since 10:00 local
    base = np.select(
        [m < 10, m < 11, m < 40, m < 50],
        [300.0, 300 - (m - 10) * 296, 4.0, 0.3], 6.0)
    noise = np.select([m < 11, m < 40, m < 50], [2.0, 0.3, 0.1], 0.4)
    down = base + rng.normal(0, 1, len(m)) * noise
    up = base + rng.normal(0, 1, len(m)) * noise
    sq = np.where((m >= 30) & (m < 40), 25.0, 85.0) + rng.normal(0, 2, len(m))
    meter_local = (true_t + pd.Timedelta(seconds=offset)).tz_convert(TZ)
    df = pd.DataFrame({
        "Date/Time": meter_local.strftime("%m/%d/%Y %H:%M:%S"),
        "CH1 Volume Flow": np.round(up, 3), "CH1 Signal Quality": np.round(sq, 1),
        "CH2 Volume Flow": np.round(down, 3), "CH2 Signal Quality": np.round(sq + 1, 1),
    }).astype(str)
    df.loc[1234, "CH2 Volume Flow"] = "----"
    df = pd.concat([df.iloc[:2000], pd.DataFrame([{c: "--- signal lost ---" if c == "Date/Time" else ""
                                                   for c in df.columns}] * 2), df.iloc[2000:]],
                   ignore_index=True)
    (out / "clampon_layout.json").write_text(json.dumps({
        "timestamp_col": "Date/Time", "upstream_flow_col": "CH1 Volume Flow",
        "upstream_quality_col": "CH1 Signal Quality", "downstream_flow_col": "CH2 Volume Flow",
        "downstream_quality_col": "CH2 Signal Quality", "skiprows": 3}, indent=2))
    with open(out / "clampon_export.csv", "w") as f:
        f.write("Meter: PORTABLE-UT-01 (synthetic)\nSite: Demo Plant / FV-101\nUnits: gpm, signal %\n")
        df.to_csv(f, index=False)
    return {"clock_offset_s": offset, "rows": len(df), "garbage_rows": 2,
            "event1": {"start_utc": "2026-11-10T15:12:00+00:00", "end_utc": "2026-11-10T15:29:50+00:00",
                       "duration_min": 18.0, "condition": "valve_closed"},
            "event2": {"start_utc_approx": "2026-11-10T15:50:00+00:00", "condition": "pump_off"}}


def generate(out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    write_mapping(out)
    expected = {"long": write_long(out, rng), "wide": write_wide(out, rng), "leakby": write_leakby(out, rng)}
    (out / "expected.json").write_text(json.dumps(expected, indent=2))
    return expected


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))
