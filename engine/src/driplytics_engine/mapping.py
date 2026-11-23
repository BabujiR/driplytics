"""Tag-mapping file: what every raw historian tag means.

CSV columns (header required, extra columns ignored):

    raw_tag        exact tag name in the export, e.g. FIT-101.PV       (required)
    canonical_tag  stable name used downstream, e.g. inlet_flow         (required)
    role           flow | pressure | level | temperature | pump_state | valve_state | other
    source_unit    unit in the export (gpm, gal, psi, degF, ...)
    target_unit    unit to store (m3/h, kPa, degC, ...)
    is_totalizer   true/false. Totalizers have a VOLUME source_unit and a FLOW target_unit
    rollover_max   counter value at which the totalizer wraps to 0 (blank = never)
    max_gap_s      longest gap (s) across which a totalizer rate is still computed (default 300)
    state_true     raw value meaning "closed" (valve) or "running" (pump), e.g. 1 / CLOSED / RUNNING
    state_false    raw value meaning "not closed" / "stopped", e.g. 0 / OPEN / STOPPED
    low_flow_cutoff  optional, in target_unit (used by the leak-by check)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .constants import Role
from .units import UnitError, convert, dimension, normalize_unit, volume_to_m3_factor

_TRUE = {"true", "1", "yes", "y", "t"}


class MappingError(ValueError):
    pass


@dataclass(frozen=True)
class TagSpec:
    raw_tag: str
    canonical_tag: str
    role: Role
    source_unit: str
    target_unit: str
    is_totalizer: bool
    rollover_max: float | None
    max_gap_s: float
    state_true: str
    state_false: str
    low_flow_cutoff: float | None


def _norm_state(v: str) -> str:
    """'1.0' -> '1', ' Closed ' -> 'closed' so numeric and text states compare cleanly."""
    s = str(v).strip().lower()
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else s
    except ValueError:
        return s


class TagMapping:
    def __init__(self, specs: list[TagSpec]):
        self.specs = {s.raw_tag: s for s in specs}
        canon = [s.canonical_tag for s in specs]
        dupes = {c for c in canon if canon.count(c) > 1}
        if dupes:
            raise MappingError(f"canonical_tag used more than once: {sorted(dupes)}")
        self.by_canonical = {s.canonical_tag: s for s in specs}

    def __contains__(self, raw_tag: str) -> bool:
        return raw_tag in self.specs

    def __getitem__(self, raw_tag: str) -> TagSpec:
        return self.specs[raw_tag]

    @property
    def raw_tags(self) -> list[str]:
        return list(self.specs)

    @classmethod
    def from_csv(cls, path: str | Path) -> TagMapping:
        return cls.from_frame(pd.read_csv(path, dtype=str, keep_default_na=False))

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> TagMapping:
        df = df.rename(columns=lambda c: str(c).strip().lower())
        for col in ("raw_tag", "canonical_tag"):
            if col not in df.columns:
                raise MappingError(f"tag mapping is missing required column '{col}'")
        specs, errors = [], []
        for i, r in df.iterrows():

            def g(k: str, d: str = "", r: pd.Series = r) -> str:
                v = r.get(k, d)
                return str(v if v is not None else d).strip()

            line = i + 2  # header is line 1
            raw, canon = g("raw_tag"), g("canonical_tag")
            if not raw or not canon:
                errors.append(f"line {line}: raw_tag and canonical_tag are required")
                continue
            try:
                role = Role(g("role", "other").lower() or "other")
            except ValueError:
                errors.append(f"line {line}: unknown role '{g('role')}'")
                continue
            src, dst = g("source_unit"), g("target_unit") or g("source_unit")
            tot = g("is_totalizer").lower() in _TRUE
            try:
                if tot:
                    volume_to_m3_factor(src)
                    if dimension(dst) != "flow":
                        raise UnitError(f"totalizer target_unit '{dst}' must be a flow unit")
                elif src and dst:
                    convert(1.0, src, dst)  # validates both units and dimensions
            except UnitError as e:
                errors.append(f"line {line} ({raw}): {e}")
                continue
            st, sf = g("state_true"), g("state_false")
            if role.is_state and (not st or not sf):
                errors.append(f"line {line} ({raw}): state tags need state_true and state_false")
                continue

            def num(k: str, g=g) -> float | None:  # type: ignore[no-untyped-def]
                return float(g(k)) if g(k) else None

            try:
                specs.append(
                    TagSpec(
                        raw_tag=raw,
                        canonical_tag=canon,
                        role=role,
                        source_unit=normalize_unit(src),
                        target_unit=normalize_unit(dst),
                        is_totalizer=tot,
                        rollover_max=num("rollover_max"),
                        max_gap_s=num("max_gap_s") or 300.0,
                        state_true=_norm_state(st) if st else "",
                        state_false=_norm_state(sf) if sf else "",
                        low_flow_cutoff=num("low_flow_cutoff"),
                    )
                )
            except ValueError as e:
                errors.append(f"line {line} ({raw}): bad number ({e})")
        if errors:
            raise MappingError("Invalid tag mapping:\n  " + "\n  ".join(errors))
        return cls(specs)
