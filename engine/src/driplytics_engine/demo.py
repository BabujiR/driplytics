"""Synthetic demo plant: "Riverbend Water Treatment (synthetic)" (P0-19). All data is made up.

A month of historian data in PI-style long format, local time (America/New_York), that tells a story
the product can find in Phase 1:

* FIT-101.PV   raw-water inlet flow (gpm): daily demand curve + noise
* FQI-101.TOT  inlet totalizer (gal): integrates FIT-101 and rolls over at 1,000,000 gal
* PIT-101.PV   inlet pressure (psi): drops a little when demand is high
* TT-101.PV    raw-water temperature (°F): slow cooling trend into winter
* P-201.RUN    high-service pump 201: RUNNING 05:00-23:00, short STOPPED breaks
* FV-101.ZSC   filter-1 backwash valve closed switch: 1 = closed; opens for 15 min every day at 02:00
* FIT-102.PV   backwash flow (gpm): ~600 gpm while backwashing, ~0 while closed...
               ...until the leak starts (default: day 12): about 4 gpm passing through the closed
               valve (leak-by), slowly worsening. This is the finding Phase 1 should rank first.

Realistic imperfections, so the import report has something to show: a 90-minute communication
outage (I/O Timeout digital states), a few Bad-quality values, and the fall-back DST hour if the window
contains the first Sunday of November.

    python -m driplytics_engine.demo --out demo/        # riverbend_30d.csv + riverbend_tag_mapping.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TZ = "America/New_York"
SITE_NAME = "Riverbend WTP"
EXPORT_NAME = "riverbend_30d.csv"
MAPPING_NAME = "riverbend_tag_mapping.csv"

MAPPING = [
    # raw_tag, canonical_tag, role, source_unit, target_unit, is_totalizer, low_flow_cutoff,
    # rollover_max, max_gap_s, state_true, state_false
    ("FIT-101.PV", "inlet_flow", "flow", "gpm", "gpm", "false", "1.0", "", "", "", ""),
    ("FQI-101.TOT", "inlet_volume_rate", "flow", "gal", "gpm", "true", "", "1000000", "600", "", ""),
    ("PIT-101.PV", "inlet_pressure", "pressure", "psi", "psi", "", "", "", "", "", ""),
    ("TT-101.PV", "raw_water_temp", "temperature", "degF", "degF", "", "", "", "", "", ""),
    ("P-201.RUN", "p201_running", "pump_state", "", "", "", "", "", "", "RUNNING", "STOPPED"),
    ("FV-101.ZSC", "fv101_closed", "valve_state", "", "", "", "", "", "", "1", "0"),
    ("FIT-102.PV", "backwash_flow", "flow", "gpm", "gpm", "false", "0.5", "", "", "", ""),
]
MAPPING_COLUMNS = [
    "raw_tag",
    "canonical_tag",
    "role",
    "source_unit",
    "target_unit",
    "is_totalizer",
    "low_flow_cutoff",
    "rollover_max",
    "max_gap_s",
    "state_true",
    "state_false",
]


@dataclass(frozen=True)
class DemoTruth:
    """What was planted, so tests (and Phase 1 checks) can verify they find it."""

    start_utc: pd.Timestamp
    end_utc: pd.Timestamp
    leak_start_utc: pd.Timestamp
    leak_gpm_start: float
    leak_gpm_end: float
    outage_start_utc: pd.Timestamp
    outage_minutes: int
    bad_quality_values: int
    rows: int


def mapping_frame() -> pd.DataFrame:
    return pd.DataFrame(MAPPING, columns=MAPPING_COLUMNS)


def generate(
    days: int = 30,
    end: str = "2026-11-23",
    interval_s: int = 60,
    leak_day: int = 12,
    seed: int = 7,
) -> tuple[pd.DataFrame, DemoTruth]:
    """Long-format export (timestamp, tag, value, quality) in local time, sorted like a PI export."""
    rng = np.random.default_rng(seed)
    end_local = pd.Timestamp(end, tz=TZ).normalize()
    start_utc = (end_local - pd.DateOffset(days=days)).tz_convert("UTC")  # local midnight, DST-aware
    t = pd.date_range(start_utc, end_local.tz_convert("UTC"), freq=f"{interval_s}s", inclusive="left")
    n = len(t)
    local = t.tz_convert(TZ)
    hour = local.hour.to_numpy() + local.minute.to_numpy() / 60.0
    day = ((t - start_utc) / pd.Timedelta(days=1)).to_numpy()

    # Inlet flow: low at night, morning and evening peaks.
    demand = 240 + 55 * np.sin((hour - 9) / 24 * 2 * np.pi) + 25 * np.sin((hour - 18) / 12 * 2 * np.pi)
    inlet = np.clip(demand + rng.normal(0, 4, n), 120, None)

    # Totalizer integrates the inlet flow and rolls over at 1,000,000 gal.
    gallons = 640_000 + np.cumsum(inlet * interval_s / 60.0)
    totalizer = np.mod(gallons, 1_000_000)

    pressure = 58 - 0.02 * (inlet - 240) + rng.normal(0, 0.3, n)
    temp = 58 - 6 * day / max(days, 1) + 0.8 * np.sin((hour - 15) / 24 * 2 * np.pi) + rng.normal(0, 0.1, n)

    # Pump 201 runs 05:00-23:00 with a 20-minute stop around 13:00 on weekdays.
    weekday = local.dayofweek.to_numpy() < 5
    pump = (hour >= 5) & (hour < 23) & ~(weekday & (hour >= 13) & (hour < 13 + 1 / 3))

    # Backwash valve FV-101: open 02:00-02:15 every day, otherwise closed.
    backwash = (hour >= 2) & (hour < 2.25)
    closed = ~backwash
    leak_start = start_utc + pd.Timedelta(days=leak_day, hours=14, minutes=7)
    leaking = t >= leak_start
    leak_progress = np.clip((t - leak_start) / (t[-1] - leak_start), 0, 1) if leaking.any() else np.zeros(n)
    leak_gpm = np.where(leaking, 3.6 + 1.4 * leak_progress, 0.0)
    backwash_flow = np.where(backwash, 600 + rng.normal(0, 15, n), leak_gpm + rng.normal(0, 0.12, n))
    backwash_flow = np.clip(backwash_flow, 0, None)

    frames = []
    for tag, values in (
        ("FIT-101.PV", np.round(inlet, 2)),
        ("FQI-101.TOT", np.round(totalizer, 1)),
        ("PIT-101.PV", np.round(pressure, 2)),
        ("TT-101.PV", np.round(temp, 2)),
        ("P-201.RUN", np.where(pump, "RUNNING", "STOPPED")),
        ("FV-101.ZSC", np.where(closed, "1", "0")),
        ("FIT-102.PV", np.round(backwash_flow, 2)),
    ):
        frames.append(pd.DataFrame({"t": t, "tag": tag, "value": values.astype(str), "quality": "Good"}))
    df = pd.concat(frames, ignore_index=True)

    # 90-minute communication outage on day 20: PI writes the digital state "I/O Timeout".
    outage_start = start_utc + pd.Timedelta(days=min(20, days - 1), hours=9, minutes=30)
    outage = (df["t"] >= outage_start) & (df["t"] < outage_start + pd.Timedelta(minutes=90))
    df.loc[outage, "value"] = "I/O Timeout"
    df.loc[outage, "quality"] = "Bad"

    # A handful of Bad-quality readings on the pressure transmitter.
    flaky = df.index[(df["tag"] == "PIT-101.PV") & ~outage]
    bad = rng.choice(flaky, size=min(12, len(flaky)), replace=False)
    df.loc[bad, "quality"] = "Bad"

    df = df.sort_values(["t", "tag"], kind="stable")
    out = pd.DataFrame(
        {
            "timestamp": df["t"].dt.tz_convert(TZ).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": df["tag"],
            "value": df["value"],
            "quality": df["quality"],
        }
    ).reset_index(drop=True)

    truth = DemoTruth(
        start_utc=start_utc,
        end_utc=t[-1],
        leak_start_utc=leak_start,
        leak_gpm_start=3.6,
        leak_gpm_end=5.0,
        outage_start_utc=outage_start,
        outage_minutes=90,
        bad_quality_values=int(outage.sum()) + len(bad),
        rows=len(out),
    )
    return out, truth


def write(out_dir: Path, **kwargs: object) -> tuple[Path, Path, DemoTruth]:
    out_dir.mkdir(parents=True, exist_ok=True)
    export, truth = generate(**kwargs)  # type: ignore[arg-type]
    export_path, mapping_path = out_dir / EXPORT_NAME, out_dir / MAPPING_NAME
    export.to_csv(export_path, index=False)
    mapping_frame().to_csv(mapping_path, index=False)
    return export_path, mapping_path, truth


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=Path("demo"))
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--end", default="2026-11-23", help="last local day (exclusive), YYYY-MM-DD")
    ap.add_argument("--interval", type=int, default=60, help="seconds between samples")
    a = ap.parse_args()
    export, mapping, truth = write(a.out, days=a.days, end=a.end, interval_s=a.interval)
    print(f"wrote {export} ({truth.rows:,} values) and {mapping}")
    print(f"planted leak-by on FV-101 from {truth.leak_start_utc.tz_convert(TZ):%Y-%m-%d %H:%M %Z}")


if __name__ == "__main__":
    main()
