"""Totalizer (cumulative volume counter) -> flow rate.

rate_i = (total_i - total_{i-1}) / (t_i - t_{i-1}), stamped at the END of the
interval (t_i), converted from <volume unit>/h to the tag's target flow unit.

Interval rules, in order:
* dt > max_gap_s            -> no rate (gap; a rate across hours of missing data is meaningless)
* delta < 0 and the counter was near rollover_max and is now near 0
                            -> ROLLOVER: delta += rollover_max
* delta < 0 otherwise       -> RESET (meter replaced / counter cleared): no rate for that interval
Rate quality = worst of the two endpoint qualities.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .mapping import TagSpec
from .units import convert, volume_to_m3_factor

ROLLOVER_HIGH = 0.9   # previous value above 90 % of rollover_max ...
ROLLOVER_LOW = 0.1    # ... and new value below 10 % of it


def totalizer_to_rate(ts_utc: pd.Series, total: np.ndarray, quality: pd.Series, spec: TagSpec
                      ) -> tuple[pd.DataFrame, list[dict], int]:
    """Inputs must be sorted by time and de-duplicated. Returns (rates, events, gap_count)."""
    if len(total) < 2:
        return pd.DataFrame({"timestamp_utc": ts_utc.iloc[:0], "value": [], "quality": []}), [], 0
    t = ts_utc.reset_index(drop=True)
    tot = np.asarray(total, dtype="float64")
    dt = t.diff().dt.total_seconds().to_numpy()[1:]
    dv = np.diff(tot)
    prev, cur = tot[:-1], tot[1:]

    valid = dt > 0
    gap = dt > spec.max_gap_s
    neg = dv < 0
    rollover = np.zeros_like(neg)
    if spec.rollover_max:
        rollover = neg & (prev >= ROLLOVER_HIGH * spec.rollover_max) & (cur <= ROLLOVER_LOW * spec.rollover_max)
        dv = np.where(rollover, dv + spec.rollover_max, dv)
    reset = neg & ~rollover
    ok = valid & ~gap & ~reset

    m3_per_h = dv * volume_to_m3_factor(spec.source_unit) / (dt / 3600.0)
    rate = convert(m3_per_h, "m3/h", spec.target_unit)

    q = quality.reset_index(drop=True).astype("string").to_numpy()
    worst = np.where((q[:-1] == "uncertain") | (q[1:] == "uncertain"), "uncertain", "good")

    end_ts = t.iloc[1:].reset_index(drop=True)
    out = pd.DataFrame({"timestamp_utc": end_ts[ok], "value": rate[ok], "quality": worst[ok]})

    events = []
    for kind, mask in (("rollover", rollover & ~gap), ("reset", reset & ~gap)):
        for i in np.flatnonzero(mask):
            events.append({"tag": spec.canonical_tag, "raw_tag": spec.raw_tag, "event": kind,
                           "timestamp_utc": end_ts.iloc[i].isoformat(),
                           "from_value": float(prev[i]), "to_value": float(cur[i])})
    return out.reset_index(drop=True), events, int((gap & valid).sum())
