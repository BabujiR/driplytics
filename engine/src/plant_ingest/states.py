"""Put discrete pump/valve state tags onto a time grid.

State tags are step signals: a value holds until the next change, so we use the
last sample at or before each grid point (as-of join), but:
* if that sample is older than max_age, the state is UNKNOWN (NaN) - stale data
  must not be trusted (historians often only store on change, so pick max_age
  to match the tag's exception/compression settings);
* for `settling` after every state change the point is flagged in_transition -
  a valve takes 30-120 s to stroke and flow takes time to decay, so we never
  judge leak-by while the valve is still moving.
"""
from __future__ import annotations

import pandas as pd


def _us_utc(s: pd.Series) -> pd.Series:
    s = pd.to_datetime(s, utc=True)
    return s.astype("datetime64[us, UTC]")


def state_on_grid(values: pd.DataFrame, tag: str, grid: pd.DatetimeIndex,
                  max_age: str | pd.Timedelta = "15min",
                  settling: str | pd.Timedelta = "120s") -> pd.DataFrame:
    """values: importer output (timestamp_utc, tag, value). Returns index=grid, state, age_s, in_transition."""
    max_age, settling = pd.Timedelta(max_age), pd.Timedelta(settling)
    s = values.loc[values["tag"].astype(str) == tag, ["timestamp_utc", "value"]]
    s = s.assign(timestamp_utc=_us_utc(s["timestamp_utc"])).sort_values("timestamp_utc")
    g = pd.DataFrame({"t": _us_utc(pd.Series(grid))})

    m = pd.merge_asof(g, s.rename(columns={"timestamp_utc": "sample_t", "value": "state"}),
                      left_on="t", right_on="sample_t", direction="backward")
    age = m["t"] - m["sample_t"]
    state = m["state"].where(age <= max_age)

    changes = s.loc[s["value"].ne(s["value"].shift()) & s["value"].shift().notna(), ["timestamp_utc"]]
    c = pd.merge_asof(g, changes.rename(columns={"timestamp_utc": "change_t"}),
                      left_on="t", right_on="change_t", direction="backward")
    in_transition = ((c["t"] - c["change_t"]) < settling).fillna(False)

    return pd.DataFrame({"state": state.to_numpy(), "age_s": age.dt.total_seconds().to_numpy(),
                         "in_transition": in_transition.to_numpy(bool)}, index=grid)
