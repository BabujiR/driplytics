"""Request/response models. Database rows are returned as plain dicts; inputs are validated here."""

import re
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

_NAME = Field(min_length=1, max_length=200)


def _check_timezone(tz: str) -> str:
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown time zone {tz!r} (use an IANA name like America/New_York)") from exc
    return tz


class SiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = _NAME
    timezone: str = "America/New_York"
    industry: Literal["water_wastewater", "food_beverage", "power", "pulp_paper", "other"] = (
        "water_wastewater"
    )
    display_units: Literal["us", "si"] = "us"

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        return _check_timezone(v)


class SiteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = None
    industry: Literal["water_wastewater", "food_beverage", "power", "pulp_paper", "other"] | None = None
    display_units: Literal["us", "si"] | None = None

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str | None) -> str | None:
        return None if v is None else _check_timezone(v)


class ExportLayoutModel(BaseModel):
    """Mirror of driplytics_engine.ExportLayout. A test keeps the two in sync."""

    model_config = ConfigDict(extra="forbid")
    format: Literal["auto", "long", "wide"] = "auto"
    timestamp_col: str = "timestamp"
    tag_col: str = "tag"
    value_col: str = "value"
    quality_col: str | None = "quality"
    quality_suffix: str | None = None
    tag_columns: list[str] | None = None
    timestamp_format: str | None = None
    sep: str = Field(default=",", min_length=1, max_length=1)
    decimal: str = Field(default=".", min_length=1, max_length=1)
    skiprows: int = Field(default=0, ge=0, le=1000)
    encoding: str = "utf-8-sig"
    wide_blank_cells: Literal["reject", "ignore"] = "reject"


class ExportProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = _NAME
    layout: ExportLayoutModel = ExportLayoutModel()


class ExportProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    layout: ExportLayoutModel | None = None


ALLOWED_UPLOAD_SUFFIXES = (".csv", ".txt", ".parquet", ".pq")


class ImportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    export_profile_id: UUID | None = None

    @field_validator("filename")
    @classmethod
    def _suffix(cls, v: str) -> str:
        if not v.lower().endswith(ALLOWED_UPLOAD_SUFFIXES):
            raise ValueError(f"file type not supported; use one of {', '.join(ALLOWED_UPLOAD_SUFFIXES)}")
        return v


def safe_filename(name: str) -> str:
    """Keep only a plain, short file name for the object key (no paths, no odd characters)."""
    base = re.split(r"[\\/]", name)[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "upload"
    return base[-120:]
