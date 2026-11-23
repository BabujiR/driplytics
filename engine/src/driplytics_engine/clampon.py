"""Milestone 2a: portable two-channel ultrasonic clamp-on flow meter export.

Typical export (Flexim FLUXUS, Siemens FUE1010, Baker Hughes PT900 style): a few
metadata lines, then one row per sample (often 1 s) with flow and signal
quality per channel. Channel 1 = upstream of the valve, channel 2 = downstream
(configurable).

Alignment to historian time:
1. Parse meter timestamps (meter local time; DST handled like the historian).
2. Correct the meter clock:  true_time = meter_time - clock_offset_s
   (clock_offset_s > 0 means the meter clock runs FAST). Measure it on site by
   noting the meter clock vs. a synced phone/SCADA clock when you install it.
3. Snap to the historian grid (default 10 s) by rounding to the nearest grid
   point; per grid point: flow = median (robust to spikes),
   signal quality = minimum (a point is only as trustworthy as its worst sample).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .timeconv import localize_to_utc, parse_timestamps
from .units import convert, normalize_unit


@dataclass
class ClampOnLayout:
    timestamp_col: str = "timestamp"
    timestamp_format: str | None = None
    timezone: str = "America/New_York"
    upstream_flow_col: str = "ch1_flow"
    upstream_quality_col: str = "ch1_signal_quality"
    downstream_flow_col: str = "ch2_flow"
    downstream_quality_col: str = "ch2_signal_quality"
    flow_unit: str = "gpm"
    sep: str = ","
    decimal: str = "."
    skiprows: int = 0
    encoding: str = "utf-8-sig"


@dataclass
class ClampOnImport:
    data: pd.DataFrame  # index timestamp_utc (grid); up_flow, up_sq, down_flow, down_sq, n_samples
    unit: str
    report: dict = field(default_factory=dict)


def _num(s: pd.Series, decimal: str) -> pd.Series:
    t = s.astype("string").str.strip()
    if decimal != ".":
        t = t.str.replace(decimal, ".", regex=False)
    return pd.to_numeric(t, errors="coerce").astype("float64")


def load_clampon_export(
    path: str | Path,
    layout: ClampOnLayout | None = None,
    clock_offset_s: float = 0.0,
    grid: str = "10s",
    target_flow_unit: str | None = None,
) -> ClampOnImport:
    lay = layout or ClampOnLayout()
    df = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        sep=lay.sep,
        skiprows=lay.skiprows,
        encoding=lay.encoding,
        skipinitialspace=True,
    )
    df = df.rename(columns=lambda c: str(c).strip())
    missing = [
        c for c in (lay.timestamp_col, lay.upstream_flow_col, lay.downstream_flow_col) if c not in df.columns
    ]
    if missing:
        raise ValueError(f"clamp-on export is missing columns {missing} (found {list(df.columns)})")

    rows = len(df)
    local = parse_timestamps(df[lay.timestamp_col], lay.timestamp_format)
    unparseable = local.isna().to_numpy()
    utc, nonexistent, _ = localize_to_utc(local, None, lay.timezone)
    utc = utc - pd.to_timedelta(clock_offset_s, unit="s")

    unit = normalize_unit(target_flow_unit or lay.flow_unit)
    raw = pd.DataFrame({"timestamp_utc": utc})
    for name, fcol, qcol in (
        ("up", lay.upstream_flow_col, lay.upstream_quality_col),
        ("down", lay.downstream_flow_col, lay.downstream_quality_col),
    ):
        raw[f"{name}_flow"] = convert(_num(df[fcol], lay.decimal), lay.flow_unit, unit)
        raw[f"{name}_sq"] = _num(df[qcol], lay.decimal) if qcol in df.columns else np.nan

    good_ts = ~unparseable & ~nonexistent
    dup_ts = raw["timestamp_utc"].duplicated(keep="first").to_numpy() & good_ts
    use = raw[good_ts & ~dup_ts].copy()
    nonnum = {c: int(use[c].isna().sum()) for c in ("up_flow", "down_flow", "up_sq", "down_sq")}

    # nearest grid point, ties up: bucket for t is [t - step/2, t + step/2).
    # (Series.dt.round rounds ties to even, which makes alternate buckets 9 and 11 samples wide.)
    use["timestamp_utc"] = (use["timestamp_utc"] + pd.Timedelta(grid) / 2).dt.floor(grid)
    g = use.groupby("timestamp_utc", sort=True)
    data = pd.DataFrame(
        {
            "up_flow": g["up_flow"].median(),
            "up_sq": g["up_sq"].min(),
            "down_flow": g["down_flow"].median(),
            "down_sq": g["down_sq"].min(),
            "n_samples": g.size(),
        }
    )
    report = {
        "source": str(path),
        "rows": rows,
        "rows_used": len(use),
        "rejected": {
            "unparseable_timestamp": int(unparseable.sum()),
            "nonexistent_local_time": int((nonexistent & ~unparseable).sum()),
            "duplicate_timestamp": int(dup_ts.sum()),
        },
        "non_numeric_cells": nonnum,
        "clock_offset_s": clock_offset_s,
        "grid": grid,
        "unit": unit,
        "first_utc": data.index.min().isoformat() if len(data) else None,
        "last_utc": data.index.max().isoformat() if len(data) else None,
    }
    assert report["rows_used"] + sum(report["rejected"].values()) == rows
    return ClampOnImport(data, unit, report)
