"""Response models (P0-13). They define the OpenAPI contract the TypeScript client is generated from.

Routes still build plain dicts from database rows; FastAPI validates them against these models
(`response_model=`), so a column that drifts from the contract fails loudly in tests instead of
silently reaching the browser. Input models live in `schemas.py`.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas import ExportLayoutModel

Industry = Literal["water_wastewater", "food_beverage", "power", "pulp_paper", "other"]
DisplayUnits = Literal["us", "si"]
Plan = Literal["pilot", "starter", "professional", "enterprise"]
RoleName = Literal["owner", "admin", "engineer", "technician", "viewer", "partner"]
TagRole = Literal["flow", "pressure", "level", "temperature", "pump_state", "valve_state", "other"]
MappingSource = Literal["manual", "rules", "behavior", "llm", "template"]
ImportStatus = Literal["pending", "uploaded", "queued", "running", "succeeded", "failed", "cancelled"]
ImportSource = Literal["upload", "connector", "demo"]


class ErrorOut(BaseModel):
    """Body of every 4xx/5xx raised by the API (validation errors use FastAPI's own 422 shape)."""

    detail: str


# Shared error responses for the OpenAPI document, so the generated client knows their shape.
COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorOut, "description": "Missing or invalid sign-in"},
    403: {"model": ErrorOut, "description": "Signed in, but not allowed"},
    404: {"model": ErrorOut, "description": "Not found (other organizations' data is never visible)"},
}


# ------------------------------------------------------------------ health and meta
class LiveOut(BaseModel):
    status: Literal["ok"]


class DependencyCheck(BaseModel):
    ok: bool
    detail: str


class ReadinessOut(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, DependencyCheck]


class VersionOut(BaseModel):
    service: str
    version: str
    env: str


# ------------------------------------------------------------------ identity
class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    last_login_at: datetime | None


class MembershipOut(BaseModel):
    tenant_id: UUID
    name: str
    slug: str
    plan: Plan
    role: RoleName


class MeOut(BaseModel):
    user: UserOut
    memberships: list[MembershipOut]


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: Plan
    created_at: datetime


class SiteSummaryOut(BaseModel):
    id: UUID
    name: str
    timezone: str
    display_units: DisplayUnits


class CurrentTenantOut(BaseModel):
    tenant: TenantOut
    role: RoleName
    sites: list[SiteSummaryOut]


# ------------------------------------------------------------------ sites, profiles, mappings
class SiteOut(BaseModel):
    id: UUID
    name: str
    timezone: str
    industry: Industry
    display_units: DisplayUnits
    created_at: datetime


class ExportProfileOut(BaseModel):
    id: UUID
    site_id: UUID
    name: str
    layout: ExportLayoutModel
    created_at: datetime


class TagMappingOut(BaseModel):
    """One known tag of a site. Every mapping field is null while the tag is unmapped."""

    tag_id: UUID
    raw_tag: str
    description: str | None
    eng_units: str | None
    canonical_tag: str | None
    role: TagRole | None
    source_unit: str | None
    target_unit: str | None
    is_totalizer: bool | None
    rollover_max: float | None
    max_gap_s: float | None
    state_true: str | None
    state_false: str | None
    low_flow_cutoff: float | None
    confidence: float | None
    source: MappingSource | None
    confirmed_at: datetime | None


class TagMappingUploadOut(BaseModel):
    site_id: UUID
    mapped_tags: int


# ------------------------------------------------------------------ imports
class ImportOut(BaseModel):
    id: UUID
    site_id: UUID
    export_profile_id: UUID | None
    source: ImportSource
    object_key: str
    original_filename: str | None
    size_bytes: int | None
    status: ImportStatus
    progress: float = Field(ge=0, le=1, description="0..1 while the worker runs")
    error: str | None
    created_by: UUID | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class UploadTarget(BaseModel):
    """Where the browser sends the file: one HTTP request straight to object storage."""

    url: str
    method: Literal["PUT"]
    headers: dict[str, str]
    expires_in: int = Field(description="seconds until the URL stops working")


class ImportCreatedOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    import_: ImportOut = Field(alias="import")
    upload: UploadTarget


class ImportSummaryOut(BaseModel):
    total_values: int
    accepted: int
    rejected: int
    duplicates: int
    rejected_by_reason: dict[str, int]
    scoring_allowed: bool


class ImportDetailOut(ImportOut):
    summary: ImportSummaryOut | None = Field(description="null until the import has succeeded")


class TotalizerEvent(BaseModel):
    tag: str
    raw_tag: str
    event: Literal["rollover", "reset"]
    timestamp_utc: str
    from_value: float
    to_value: float


class TagSummary(BaseModel):
    tag: str
    raw_tag: str
    role: TagRole
    unit: str
    accepted_inputs: int
    output_rows: int
    first_utc: str | None
    last_utc: str | None


class RejectedExample(BaseModel):
    seq: int = Field(description="position of the value in the file")
    raw_tag: str | None
    timestamp: str | None
    value: str | None


class ImportReportOut(BaseModel):
    """The engine's ImportReport (accepted + rejected + duplicates = total_values, always)."""

    source: str
    format: str
    timezone: str
    total_values: int
    accepted: int
    rejected: int
    duplicates: int
    rejected_by_reason: dict[str, int]
    accepted_uncertain: int
    unmapped_tags: dict[str, int] = Field(description="raw tag -> number of values")
    scoring_allowed: bool
    scoring_blocked_reasons: list[str]
    dst: dict[str, int]
    totalizer_events: list[TotalizerEvent]
    totalizer_gaps: int
    tags: list[TagSummary]
    blank_cells_ignored: int
    rejected_examples: dict[str, list[RejectedExample]] = Field(description="up to 20 per reason")
    elapsed_s: float
    values_per_second: float
    output_path: str | None


# ------------------------------------------------------------------ audit
class AuditEventOut(BaseModel):
    id: UUID
    at: datetime
    action: str
    entity_type: str | None
    entity_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    user_email: str | None
