"""Linear unit conversion: base = value * scale + offset.

Each dimension has a base unit. Converting src -> dst goes src -> base -> dst.
Unit names are case-insensitive and whitespace-insensitive.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# unit -> (dimension, scale_to_base, offset_to_base)
_UNITS: dict[str, tuple[str, float, float]] = {
    # volume, base m3
    "m3": ("volume", 1.0, 0.0),
    "l": ("volume", 1e-3, 0.0),
    "ml": ("volume", 1e3, 0.0),          # megalitre (water-industry usage)
    "gal": ("volume", 0.003785411784, 0.0),
    "kgal": ("volume", 3.785411784, 0.0),
    "mg": ("volume", 3785.411784, 0.0),   # million US gallons
    "ft3": ("volume", 0.028316846592, 0.0),
    "af": ("volume", 1233.48183754752, 0.0),  # acre-foot
    # volumetric flow, base m3/h
    "m3/h": ("flow", 1.0, 0.0),
    "m3/s": ("flow", 3600.0, 0.0),
    "l/s": ("flow", 3.6, 0.0),
    "l/min": ("flow", 0.06, 0.0),
    "gpm": ("flow", 0.227124707, 0.0),
    "gph": ("flow", 0.003785411784, 0.0),
    "mgd": ("flow", 157.725491, 0.0),
    "cfs": ("flow", 101.9406477312, 0.0),
    # pressure, base kPa
    "kpa": ("pressure", 1.0, 0.0),
    "pa": ("pressure", 1e-3, 0.0),
    "bar": ("pressure", 100.0, 0.0),
    "psi": ("pressure", 6.894757293168, 0.0),
    "inh2o": ("pressure", 0.24884, 0.0),
    # length / level, base m
    "m": ("length", 1.0, 0.0),
    "cm": ("length", 0.01, 0.0),
    "mm": ("length", 0.001, 0.0),
    "ft": ("length", 0.3048, 0.0),
    "in": ("length", 0.0254, 0.0),
    # temperature, base degC
    "degc": ("temperature", 1.0, 0.0),
    "degf": ("temperature", 5.0 / 9.0, -32.0 * 5.0 / 9.0),
    "k": ("temperature", 1.0, -273.15),
    # dimensionless
    "%": ("ratio", 1.0, 0.0),
    "fraction": ("ratio", 100.0, 0.0),
}

_ALIASES = {
    "m³": "m3", "m³/h": "m3/h", "m3/hr": "m3/h", "cmh": "m3/h", "lps": "l/s",
    "gallons": "gal", "usgal": "gal", "us gal": "gal", "gal/min": "gpm", "usgpm": "gpm",
    "°c": "degc", "c": "degc", "°f": "degf", "f": "degf", "psig": "psi", "percent": "%",
    "cf": "ft3", "cuft": "ft3", "mgal": "mg",
}


class UnitError(ValueError):
    pass


def normalize_unit(unit: str | None) -> str:
    if unit is None:
        return ""
    u = str(unit).strip().lower().replace(" ", "")
    return _ALIASES.get(u, u)


def dimension(unit: str) -> str:
    u = normalize_unit(unit)
    if u not in _UNITS:
        raise UnitError(f"Unknown unit '{unit}'")
    return _UNITS[u][0]


def convert(values, src: str | None, dst: str | None):
    """Convert a scalar or numpy/pandas array from src to dst. Blank units mean 'no conversion'."""
    s, d = normalize_unit(src), normalize_unit(dst)
    if not s or not d or s == d:
        return values
    for u, orig in ((s, src), (d, dst)):
        if u not in _UNITS:
            raise UnitError(f"Unknown unit '{orig}'")
    ds, ss, so = _UNITS[s]
    dd, ds_, do = _UNITS[d]
    if ds != dd:
        raise UnitError(f"Cannot convert {src} ({ds}) to {dst} ({dd})")
    out = (np.asarray(values, dtype="float64") * ss + so - do) / ds_
    if isinstance(values, pd.Series):
        return pd.Series(out, index=values.index, name=values.name)
    if np.isscalar(values):
        return float(out)
    return out


def volume_to_m3_factor(unit: str) -> float:
    u = normalize_unit(unit)
    if u not in _UNITS or _UNITS[u][0] != "volume":
        raise UnitError(f"Totalizer unit '{unit}' is not a volume unit")
    return _UNITS[u][1]
