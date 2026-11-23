"""Normalize vendor quality flags to GOOD / UNCERTAIN / BAD.

Sources handled:
* OPC DA numeric quality (0-255): bits 7-6 -> 00 bad, 01 uncertain, 11 good.
* Text flags from PI / IP.21 / generic exports ("Good", "Suspect", "Bad", ...).
* PI "digital states" that appear in the VALUE column instead of a number
  ("Bad Input", "I/O Timeout", ...). Those are detected by is_digital_state().

Unknown text flags are treated as BAD (conservative: never score on data we
cannot vouch for). Blank quality is configurable; default GOOD because many
exports (especially wide format) simply have no quality column.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import Quality

_GOOD = {"good", "g", "ok", "valid", "normal", "0x00c0", "gd"}
_UNCERTAIN = {"uncertain", "suspect", "questionable", "substituted", "manual", "manual entry",
              "estimated", "interpolated", "uncertain_last_usable", "doubtful", "u"}
_BAD = {"bad", "b", "invalid", "fail", "failed", "error", "no data", "nodata", "offline",
        "comm fail", "not connected", "out of service", "bad quality"}

# OSIsoft PI system digital state set (common members) + IP.21-style status words.
PI_DIGITAL_STATES = {
    "bad input", "i/o timeout", "comm fail", "shutdown", "calc failed", "calc timeout",
    "no data", "pt created", "scan off", "scan timeout", "under range", "over range",
    "bad", "configure", "out of serv", "failed", "error", "not connected", "intf shut",
    "arc off-line", "no result", "bad data", "doubtful", "equip fail", "invalid data",
    "no sample", "set to bad", "trace", "unit down", "access denied", "bad quality",
    "invalid float", "no alarm", "#value!", "n/a", "nan",
}


def _classify_text(flag: str, blank: Quality) -> Quality:
    f = flag.strip().lower()
    if f == "":
        return blank
    try:
        code = int(float(f))
        top = (code >> 6) & 0b11
        return {0b11: Quality.GOOD, 0b01: Quality.UNCERTAIN}.get(top, Quality.BAD)
    except ValueError:
        pass
    if f in _GOOD:
        return Quality.GOOD
    if f in _UNCERTAIN:
        return Quality.UNCERTAIN
    return Quality.BAD  # explicit bad or unknown


def normalize_quality(raw: pd.Series | None, n: int, blank: Quality = Quality.GOOD) -> pd.Series:
    """Return a categorical Series of Quality values. Maps unique values only (fast on 100M+ rows)."""
    cats = [q.value for q in Quality]
    if raw is None:
        return pd.Series(pd.Categorical([blank.value] * n, categories=cats))
    if pd.api.types.is_numeric_dtype(raw):
        code = raw.fillna(-1).astype("int64").to_numpy()
        top = (code >> 6) & 0b11
        out = np.where(code < 0, blank.value,
                       np.where(top == 0b11, "good", np.where(top == 0b01, "uncertain", "bad")))
        return pd.Series(pd.Categorical(out, categories=cats), index=raw.index)
    as_cat = raw.astype("string").fillna("").astype("category")
    mapping = {c: _classify_text(str(c), blank).value for c in as_cat.cat.categories}
    return pd.Series(pd.Categorical(as_cat.map(mapping).astype("string"), categories=cats),
                     index=raw.index)


def is_digital_state(values: pd.Series) -> pd.Series:
    """True where a text value is a known PI/IP.21 system state rather than a measurement."""
    low = values.astype("string").str.strip().str.lower()
    return low.isin(PI_DIGITAL_STATES).fillna(False).astype(bool)
