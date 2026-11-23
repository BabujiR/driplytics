"""Milestone 2b: valve leak-by check.

At each grid point the check asks: is the valve reporting CLOSED (or the pump
reporting OFF), is the clamp-on signal trustworthy, and is flow still above the
meter's low-flow cutoff? Sustained "yes" for at least min_duration = an event,
explained in plain words. The check never guesses: if a required tag is missing
it returns SKIPPED and says why.

Status values
    FLAGGED       one or more leak-by events
    CLEAR         valve closed / pump off with good signal for some time, flow stayed at/below cutoff
    INCONCLUSIVE  inputs present, but no time in the window could be evaluated (e.g. valve never closed)
    SKIPPED       a required input is missing or the historian import blocked scoring
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .clampon import ClampOnImport
from .report import ImportReport
from .states import state_on_grid
from .units import convert, normalize_unit

Status = Literal["FLAGGED", "CLEAR", "INCONCLUSIVE", "SKIPPED"]


@dataclass
class LeakByConfig:
    valve_state_tag: str | None = None  # canonical tag, value 1.0 = CLOSED
    pump_state_tag: str | None = None  # canonical tag, value 1.0 = RUNNING
    valve_label: str | None = None  # name used in messages (default: the tag)
    pump_label: str | None = None
    flow_channel: Literal["downstream", "upstream"] = "downstream"
    low_flow_cutoff: float = 0.0  # meter low-flow cutoff, in flow_unit
    flow_unit: str = "gpm"
    min_signal_quality: float = 60.0  # same scale as the meter export (% here)
    min_duration: str = "5min"  # sustained this long before we flag
    settling_time: str = "120s"  # ignore this long after a valve/pump state change
    max_state_age: str = "15min"  # older state samples count as unknown
    max_gap: str = "30s"  # holes allowed inside one event


@dataclass
class LeakByResult:
    status: Status
    reasons: list[str]
    events: pd.DataFrame = field(default_factory=pd.DataFrame)
    timeline: pd.DataFrame = field(default_factory=pd.DataFrame)
    summary: dict = field(default_factory=dict)


EVENT_COLUMNS = [
    "start_utc",
    "end_utc",
    "duration_min",
    "condition",
    "channel",
    "mean_flow",
    "peak_flow",
    "upstream_mean_flow",
    "min_signal_quality",
    "unit",
    "reason",
]


def _skip(reasons: list[str]) -> LeakByResult:
    return LeakByResult("SKIPPED", reasons, pd.DataFrame(columns=EVENT_COLUMNS))


def _fmt_t(t: pd.Timestamp) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S")


def run_leak_by_check(
    clampon: ClampOnImport,
    historian_values: pd.DataFrame,
    config: LeakByConfig,
    import_report: ImportReport | None = None,
) -> LeakByResult:
    c = config
    unit = normalize_unit(c.flow_unit)
    ch = "down" if c.flow_channel == "downstream" else "up"

    # ---- 1. required inputs: say exactly what is missing, never guess ----------------------
    reasons: list[str] = []
    if import_report is not None and not import_report.scoring_allowed:
        reasons.append(
            "Historian import blocked scoring: " + "; ".join(import_report.scoring_blocked_reasons) + "."
        )
    if not c.valve_state_tag and not c.pump_state_tag:
        reasons.append(
            "No valve position or pump run-status tag is configured, so there is nothing to "
            "compare the flow against."
        )
    known = set(historian_values["tag"].astype(str).unique()) if len(historian_values) else set()
    for tag, what in ((c.valve_state_tag, "valve position"), (c.pump_state_tag, "pump run status")):
        if tag and tag not in known:
            reasons.append(f"Required {what} tag '{tag}' is missing from the historian data.")
    data = clampon.data
    if data.empty:
        reasons.append("The clamp-on export has no usable readings.")
    else:
        if data[f"{ch}_flow"].isna().all():
            reasons.append(f"The clamp-on export has no {c.flow_channel} flow readings.")
        if data[f"{ch}_sq"].isna().all():
            reasons.append(
                f"The clamp-on export has no {c.flow_channel} signal-quality readings, so "
                "flow readings cannot be trusted."
            )
    if reasons:
        return _skip(reasons)

    # ---- 2. timeline on the clamp-on grid -------------------------------------------------
    grid = data.index
    flow = pd.Series(convert(data[f"{ch}_flow"].to_numpy(), clampon.unit, unit), index=grid)
    up_flow = pd.Series(convert(data["up_flow"].to_numpy(), clampon.unit, unit), index=grid)
    sq = data[f"{ch}_sq"]

    tl = pd.DataFrame({"flow": flow, "signal_quality": sq}, index=grid)
    closed = off = pd.Series(False, index=grid)
    unknown = pd.Series(True, index=grid)
    transition = pd.Series(False, index=grid)
    for tag, kind in ((c.valve_state_tag, "valve"), (c.pump_state_tag, "pump")):
        if not tag:
            continue
        st = state_on_grid(historian_values, tag, grid, c.max_state_age, c.settling_time)
        if st["state"].isna().all():
            return _skip(
                [
                    f"Tag '{tag}' has no samples within {c.max_state_age} of the clamp-on "
                    f"window ({_fmt_t(grid[0])} to {_fmt_t(grid[-1])} UTC)."
                ]
            )
        tl[f"{kind}_state"] = st["state"]
        tl[f"{kind}_in_transition"] = st["in_transition"]
        transition |= st["in_transition"]
        unknown &= st["state"].isna()
        if kind == "valve":
            closed = (st["state"] == 1.0) & ~st["in_transition"]
        else:
            off = (st["state"] == 0.0) & ~st["in_transition"]

    condition = closed | off
    sq_ok = sq >= c.min_signal_quality
    evaluable = condition & sq_ok & flow.notna()
    suspicious = evaluable & (flow > c.low_flow_cutoff)
    tl["valve_closed"], tl["pump_off"] = closed, off
    tl["evaluable"], tl["suspicious"] = evaluable, suspicious

    step = pd.Series(grid).diff().median() if len(grid) > 1 else pd.Timedelta("10s")
    step_min = step.total_seconds() / 60
    summary = {
        "window_start_utc": grid[0].isoformat(),
        "window_end_utc": grid[-1].isoformat(),
        "grid_step_s": step.total_seconds(),
        "points": len(grid),
        "minutes_valve_closed": round(float(closed.sum()) * step_min, 1),
        "minutes_pump_off": round(float(off.sum()) * step_min, 1),
        "minutes_in_transition": round(float(transition.sum()) * step_min, 1),
        "minutes_state_unknown": round(float(unknown.sum()) * step_min, 1),
        "minutes_excluded_poor_signal": round(float((condition & ~sq_ok).sum()) * step_min, 1),
        "minutes_evaluated": round(float(evaluable.sum()) * step_min, 1),
        "minutes_above_cutoff": round(float(suspicious.sum()) * step_min, 1),
        "low_flow_cutoff": c.low_flow_cutoff,
        "unit": unit,
        "channel": c.flow_channel,
    }

    # ---- 3. group suspicious points into sustained events -----------------------------------
    events = []
    ts = pd.Series(grid[suspicious.to_numpy()])
    if len(ts):
        run_id = (ts.diff() > pd.Timedelta(c.max_gap)).cumsum()
        for _, run in ts.groupby(run_id):
            start, end = run.iloc[0], run.iloc[-1]
            dur = end - start + step
            if dur < pd.Timedelta(c.min_duration):
                continue
            sel = suspicious & (grid >= start) & (grid <= end)
            v_cl, p_off = bool(closed[sel].any()), bool(off[sel].any())
            parts = []
            if v_cl:
                parts.append(f"valve {c.valve_label or c.valve_state_tag} reported CLOSED")
            if p_off:
                parts.append(f"pump {c.pump_label or c.pump_state_tag} reported OFF")
            cond_txt = " and ".join(parts)
            mean, peak = float(flow[sel].mean()), float(flow[sel].max())
            up_mean = float(up_flow[sel].mean()) if c.flow_channel == "downstream" else np.nan
            min_sq = float(sq[sel].min())
            meaning = (
                "Flow past a closed valve suggests the valve is leaking by."
                if v_cl
                else "Flow with the pump off suggests a leaking check valve, backflow, or another "
                "source feeding the line."
            )
            reason = (
                f"{c.flow_channel.capitalize()} flow averaged {mean:.1f} {unit} (peak {peak:.1f} {unit}), "
                f"above the meter's low-flow cutoff of {c.low_flow_cutoff:g} {unit}, for "
                f"{dur.total_seconds() / 60:.1f} minutes from {_fmt_t(start)} to {_fmt_t(end)} UTC "
                f"while {cond_txt}. Signal quality stayed at or above {min_sq:.0f}."
                + (f" Upstream channel averaged {up_mean:.1f} {unit}." if not np.isnan(up_mean) else "")
                + f" {meaning}"
            )
            events.append(
                {
                    "start_utc": start,
                    "end_utc": end,
                    "duration_min": round(dur.total_seconds() / 60, 1),
                    "condition": "valve_closed"
                    if v_cl and not p_off
                    else "pump_off"
                    if p_off and not v_cl
                    else "valve_closed+pump_off",
                    "channel": c.flow_channel,
                    "mean_flow": round(mean, 3),
                    "peak_flow": round(peak, 3),
                    "upstream_mean_flow": round(up_mean, 3),
                    "min_signal_quality": min_sq,
                    "unit": unit,
                    "reason": reason,
                }
            )
    ev = pd.DataFrame(events, columns=EVENT_COLUMNS)

    notes = []
    if summary["minutes_excluded_poor_signal"]:
        notes.append(
            f"{summary['minutes_excluded_poor_signal']} minutes were not judged because clamp-on "
            f"signal quality was below {c.min_signal_quality:g}."
        )
    if summary["minutes_state_unknown"]:
        notes.append(
            f"{summary['minutes_state_unknown']} minutes were not judged because the valve/pump "
            f"state was older than {c.max_state_age}."
        )

    if len(ev):
        return LeakByResult("FLAGGED", list(ev["reason"]) + notes, ev, tl, summary)
    if summary["minutes_evaluated"] == 0:
        return LeakByResult(
            "INCONCLUSIVE",
            [
                "No time in the clamp-on window had the valve reporting closed or the pump reporting off "
                "with good signal quality, so leak-by could not be judged.",
                *notes,
            ],
            ev,
            tl,
            summary,
        )
    msg = (
        f"Checked {summary['minutes_evaluated']} minutes with the valve closed or pump off and good "
        f"signal; {c.flow_channel} flow stayed at or below the {c.low_flow_cutoff:g} {unit} cutoff"
    )
    if summary["minutes_above_cutoff"]:
        msg += (
            f" except for {summary['minutes_above_cutoff']} minutes in bursts shorter than {c.min_duration}"
        )
    return LeakByResult("CLEAR", [msg + ".", *notes], ev, tl, summary)
