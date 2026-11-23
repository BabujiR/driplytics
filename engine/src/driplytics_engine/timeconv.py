"""Timestamp parsing and local -> UTC conversion with daylight-saving handling.

Historian exports are usually written in plant local time WITHOUT a UTC offset.
Two days a year that is lossy:

* Spring forward (e.g. 2026-03-08 in US zones): 02:00:00-02:59:59 never happens.
  Such timestamps are reported as NONEXISTENT_LOCAL_TIME (we never guess).
* Fall back (e.g. 2026-11-01): 01:00:00-01:59:59 happens twice. A 10 s tag then
  shows ... 01:59:40, 01:59:50, 01:00:00, 01:00:10 ... The first pass is
  daylight time (UTC-4), the second pass is standard time (UTC-5).

We resolve the repeated hour from FILE ORDER, per tag: inside the ambiguous
hour, the first backwards jump in local time marks the start of the second
pass. Exact repeats that do not jump backwards stay in the first pass (and later
become duplicates). Assumption, documented in the README: each tag's rows are in
ascending time order in the export, which is how PI and IP.21 write them.

Timestamps that already carry an offset ("...-04:00" or "Z") or are tz-aware in
Parquet are converted directly; no guessing is needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

_OFFSET_RE = re.compile(r"(?:Z|[+-]\d{2}:?\d{2})\s*$")


def parse_timestamps(raw: pd.Series, fmt: str | None = None) -> pd.Series:
    """Parse to datetime64. Returns naive local times, or tz-aware UTC if the input has offsets.

    Unparseable values become NaT (the caller rejects them as UNPARSEABLE_TIMESTAMP).
    """
    if isinstance(raw.dtype, pd.DatetimeTZDtype):
        return raw.dt.tz_convert("UTC")
    if pd.api.types.is_datetime64_dtype(raw):
        return raw
    s = raw.astype("string").str.strip()
    sample = s.dropna()
    sample = sample[sample != ""].head(50)
    has_offset = len(sample) > 0 and sample.str.contains(_OFFSET_RE).mean() > 0.5
    kw = dict(errors="coerce", utc=has_offset)
    if fmt:
        return pd.to_datetime(s, format=fmt, **kw)
    out = pd.to_datetime(s, format="ISO8601", **kw)
    if out.isna().mean() > 0.5 and len(sample):  # not ISO; fall back to pandas inference
        out = pd.to_datetime(s, format="mixed", **kw)
    return out


@dataclass
class LocalizeStats:
    ambiguous_first_pass: int = 0
    ambiguous_second_pass: int = 0
    nonexistent: int = 0

    def add(self, other: LocalizeStats) -> None:
        self.ambiguous_first_pass += other.ambiguous_first_pass
        self.ambiguous_second_pass += other.ambiguous_second_pass
        self.nonexistent += other.nonexistent


def localize_to_utc(
    local: pd.Series, group: pd.Series | None, tz: str
) -> tuple[pd.Series, np.ndarray, LocalizeStats]:
    """Convert naive local timestamps (in file order) to UTC.

    Returns (utc_series, nonexistent_mask, stats). NaT inputs stay NaT and are not
    counted as nonexistent (they were already rejected as unparseable).
    """
    n = len(local)
    if isinstance(local.dtype, pd.DatetimeTZDtype):
        return local.dt.tz_convert("UTC"), np.zeros(n, bool), LocalizeStats()
    if tz.upper() in ("UTC", "ETC/UTC", "Z"):
        return local.dt.tz_localize("UTC"), np.zeros(n, bool), LocalizeStats()

    dst = local.dt.tz_localize(tz, ambiguous=np.ones(n, bool), nonexistent="NaT")
    std = local.dt.tz_localize(tz, ambiguous=np.zeros(n, bool), nonexistent="NaT")
    nonexistent = (local.notna() & dst.isna()).to_numpy()
    amb = (dst.notna() & (dst != std)).to_numpy()
    second = np.zeros(n, bool)

    if amb.any():
        idx = np.flatnonzero(amb)
        l_amb = local.iloc[idx]
        keys = [
            group.iloc[idx].to_numpy() if group is not None else np.zeros(len(idx)),
            l_amb.dt.floor("D").to_numpy(),
        ]
        # previous ambiguous row of the same tag on the same day, in file order
        prev = l_amb.groupby(keys, sort=False).shift()
        jump = (l_amb < prev).astype("int8")
        second[idx] = jump.groupby(keys, sort=False).cummax().to_numpy().astype(bool)

    utc = dst.where(~pd.Series(second, index=local.index), std).dt.tz_convert("UTC")
    stats = LocalizeStats(int(amb.sum() - second.sum()), int(second.sum()), int(nonexistent.sum()))
    return utc, nonexistent, stats
