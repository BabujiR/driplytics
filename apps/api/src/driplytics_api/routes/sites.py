"""Sites, export profiles and tag mappings (P0-10). All reads/writes go through row-level security."""

import io
from contextlib import AbstractContextManager
from typing import Annotated, Any
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from psycopg import errors
from psycopg.types.json import Jsonb

from driplytics_api import audit
from driplytics_api.auth.deps import TenantContext, require_role
from driplytics_api.auth.roles import Role
from driplytics_api.db.connection import Conn, request_tx
from driplytics_api.responses import (
    COMMON_ERRORS,
    ErrorOut,
    ExportProfileOut,
    SiteOut,
    TagMappingOut,
    TagMappingUploadOut,
)
from driplytics_api.schemas import ExportProfileCreate, ExportProfileUpdate, SiteCreate, SiteUpdate
from driplytics_api.settings import Settings, get_settings
from driplytics_engine import TagMapping
from driplytics_engine.mapping import MappingError

router = APIRouter(prefix="/api/v1", tags=["sites"], responses=COMMON_ERRORS)
CONFLICT: dict[int | str, dict[str, Any]] = {409: {"model": ErrorOut, "description": "Name already in use"}}

Viewer = Annotated[TenantContext, Depends(require_role(Role.VIEWER))]
Engineer = Annotated[TenantContext, Depends(require_role(Role.ENGINEER))]
Admin = Annotated[TenantContext, Depends(require_role(Role.ADMIN))]
SettingsDep = Annotated[Settings, Depends(get_settings)]

SITE_COLS = "id, name, timezone, industry, display_units, created_at"
PROFILE_COLS = "id, site_id, name, layout, created_at"
MAX_MAPPING_BYTES = 5 * 1024 * 1024


def _tx(settings: Settings, ctx: TenantContext) -> AbstractContextManager[Conn]:
    return request_tx(settings.database_url, user_id=ctx.principal.user_id, tenant_id=ctx.tenant_id)


def _not_found(what: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"{what} not found")


def _get_site(conn: Conn, site_id: UUID) -> dict[str, Any]:
    row = conn.execute(f"SELECT {SITE_COLS} FROM site WHERE id = %s", (site_id,)).fetchone()
    if row is None:
        raise _not_found("site")  # also for other tenants' sites: RLS hides them
    return row


# ------------------------------------------------------------------ sites
@router.get("/sites", response_model=list[SiteOut])
def list_sites(ctx: Viewer, settings: SettingsDep) -> list[dict[str, Any]]:
    with _tx(settings, ctx) as conn:
        return conn.execute(f"SELECT {SITE_COLS} FROM site ORDER BY name").fetchall()


@router.post("/sites", status_code=status.HTTP_201_CREATED, response_model=SiteOut, responses=CONFLICT)
def create_site(body: SiteCreate, ctx: Admin, settings: SettingsDep) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        try:
            with conn.transaction():
                row = conn.execute(
                    f"INSERT INTO site (tenant_id, name, timezone, industry, display_units) "
                    f"VALUES (%s, %s, %s, %s, %s) RETURNING {SITE_COLS}",
                    (ctx.tenant_id, body.name, body.timezone, body.industry, body.display_units),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"a site named {body.name!r} already exists"
            ) from exc
        assert row is not None
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="site.create",
            entity_type="site",
            entity_id=row["id"],
            after=row,
        )
        return row


@router.get("/sites/{site_id}", response_model=SiteOut)
def get_site(site_id: UUID, ctx: Viewer, settings: SettingsDep) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        return _get_site(conn, site_id)


@router.patch("/sites/{site_id}", response_model=SiteOut, responses=CONFLICT)
def update_site(site_id: UUID, body: SiteUpdate, ctx: Engineer, settings: SettingsDep) -> dict[str, Any]:
    changes = body.model_dump(exclude_none=True)
    with _tx(settings, ctx) as conn:
        before = _get_site(conn, site_id)
        if not changes:
            return before
        sets = ", ".join(f"{k} = %({k})s" for k in changes)  # keys come from the pydantic model, not the user
        try:
            with conn.transaction():
                after = conn.execute(
                    f"UPDATE site SET {sets} WHERE id = %(id)s RETURNING {SITE_COLS}",
                    {**changes, "id": site_id},
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "another site already has that name") from exc
        assert after is not None
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="site.update",
            entity_type="site",
            entity_id=site_id,
            before=before,
            after=after,
        )
        return after


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: UUID, ctx: Admin, settings: SettingsDep) -> None:
    """Deletes the site and everything under it (areas, assets, tags, mappings, imports)."""
    with _tx(settings, ctx) as conn:
        before = _get_site(conn, site_id)
        conn.execute("DELETE FROM site WHERE id = %s", (site_id,))
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="site.delete",
            entity_type="site",
            entity_id=site_id,
            before=before,
        )


# ------------------------------------------------------------------ export profiles
@router.get("/sites/{site_id}/export-profiles", response_model=list[ExportProfileOut])
def list_export_profiles(site_id: UUID, ctx: Viewer, settings: SettingsDep) -> list[dict[str, Any]]:
    with _tx(settings, ctx) as conn:
        _get_site(conn, site_id)
        return conn.execute(
            f"SELECT {PROFILE_COLS} FROM export_profile WHERE site_id = %s ORDER BY name",
            (site_id,),
        ).fetchall()


@router.post(
    "/sites/{site_id}/export-profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=ExportProfileOut,
    responses=CONFLICT,
)
def create_export_profile(
    site_id: UUID, body: ExportProfileCreate, ctx: Engineer, settings: SettingsDep
) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        _get_site(conn, site_id)
        try:
            with conn.transaction():
                row = conn.execute(
                    f"INSERT INTO export_profile (tenant_id, site_id, name, layout) VALUES (%s, %s, %s, %s) "
                    f"RETURNING {PROFILE_COLS}",
                    (ctx.tenant_id, site_id, body.name, Jsonb(body.layout.model_dump())),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, f"profile {body.name!r} already exists") from exc
        assert row is not None
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="export_profile.create",
            entity_type="export_profile",
            entity_id=row["id"],
            after=row,
        )
        return row


@router.patch("/export-profiles/{profile_id}", response_model=ExportProfileOut)
def update_export_profile(
    profile_id: UUID, body: ExportProfileUpdate, ctx: Engineer, settings: SettingsDep
) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        before = conn.execute(
            f"SELECT {PROFILE_COLS} FROM export_profile WHERE id = %s",
            (profile_id,),
        ).fetchone()
        if before is None:
            raise _not_found("export profile")
        name = body.name if body.name is not None else before["name"]
        layout = body.layout.model_dump() if body.layout is not None else before["layout"]
        after = conn.execute(
            f"UPDATE export_profile SET name = %s, layout = %s WHERE id = %s RETURNING {PROFILE_COLS}",
            (name, Jsonb(layout), profile_id),
        ).fetchone()
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="export_profile.update",
            entity_type="export_profile",
            entity_id=profile_id,
            before=before,
            after=after,
        )
        assert after is not None
        return after


# ------------------------------------------------------------------ tag mappings
@router.get("/sites/{site_id}/tag-mappings", response_model=list[TagMappingOut])
def list_tag_mappings(site_id: UUID, ctx: Viewer, settings: SettingsDep) -> list[dict[str, Any]]:
    """Every known tag of the site, mapped or not (unmapped tags have role = null)."""
    with _tx(settings, ctx) as conn:
        _get_site(conn, site_id)
        return conn.execute(
            "SELECT t.id AS tag_id, t.raw_tag, t.description, t.eng_units, m.canonical_tag, m.role, "
            "m.source_unit, m.target_unit, m.is_totalizer, m.rollover_max, m.max_gap_s, m.state_true, "
            "m.state_false, m.low_flow_cutoff, m.confidence, m.source, m.confirmed_at "
            "FROM tag t LEFT JOIN tag_mapping m ON m.tag_id = t.id WHERE t.site_id = %s ORDER BY t.raw_tag",
            (site_id,),
        ).fetchall()


@router.put(
    "/sites/{site_id}/tag-mappings/csv",
    response_model=TagMappingUploadOut,
    responses={413: {"model": ErrorOut, "description": "File larger than 5 MB"}},
)
def upload_tag_mapping_csv(
    site_id: UUID, file: UploadFile, ctx: Engineer, settings: SettingsDep
) -> dict[str, Any]:
    """Upsert mappings from a tag_mapping.csv (engine format). Validated by the engine first:
    any invalid line rejects the whole file with every problem listed."""
    content = file.file.read(MAX_MAPPING_BYTES + 1)
    if len(content) > MAX_MAPPING_BYTES:
        raise HTTPException(413, "mapping file is larger than 5 MB")
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding="utf-8-sig")
        mapping = TagMapping.from_frame(frame)
    except MappingError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise HTTPException(422, f"could not read CSV: {exc}") from exc

    with _tx(settings, ctx) as conn:
        _get_site(conn, site_id)
        for spec in mapping.specs.values():
            tag = conn.execute(
                "INSERT INTO tag (tenant_id, site_id, raw_tag) VALUES (%s, %s, %s) "
                "ON CONFLICT (site_id, raw_tag) DO UPDATE SET raw_tag = EXCLUDED.raw_tag RETURNING id",
                (ctx.tenant_id, site_id, spec.raw_tag),
            ).fetchone()
            assert tag is not None
            conn.execute(
                "INSERT INTO tag_mapping (tag_id, tenant_id, canonical_tag, role, source_unit, target_unit, "
                "is_totalizer, rollover_max, max_gap_s, state_true, state_false, low_flow_cutoff, confidence, "
                "source, confirmed_by, confirmed_at, updated_at) "
                "VALUES (%(tag)s, %(t)s, %(c)s, %(role)s, %(su)s, %(tu)s, %(tot)s, %(ro)s, %(gap)s, %(st)s, %(sf)s, "
                "%(lfc)s, 1.0, 'manual', %(u)s, now(), now()) "
                "ON CONFLICT (tag_id) DO UPDATE SET canonical_tag = EXCLUDED.canonical_tag, role = EXCLUDED.role, "
                "source_unit = EXCLUDED.source_unit, target_unit = EXCLUDED.target_unit, "
                "is_totalizer = EXCLUDED.is_totalizer, rollover_max = EXCLUDED.rollover_max, "
                "max_gap_s = EXCLUDED.max_gap_s, state_true = EXCLUDED.state_true, "
                "state_false = EXCLUDED.state_false, low_flow_cutoff = EXCLUDED.low_flow_cutoff, "
                "confidence = 1.0, source = 'manual', confirmed_by = EXCLUDED.confirmed_by, "
                "confirmed_at = now(), updated_at = now()",
                {
                    "tag": tag["id"],
                    "t": ctx.tenant_id,
                    "c": spec.canonical_tag,
                    "role": spec.role.value,
                    "su": spec.source_unit or None,
                    "tu": spec.target_unit or None,
                    "tot": spec.is_totalizer,
                    "ro": spec.rollover_max,
                    "gap": spec.max_gap_s,
                    "st": spec.state_true or None,
                    "sf": spec.state_false or None,
                    "lfc": spec.low_flow_cutoff,
                    "u": ctx.principal.user_id,
                },
            )
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="tag_mapping.import",
            entity_type="site",
            entity_id=site_id,
            after={"file": file.filename, "tags": sorted(mapping.raw_tags)},
        )
    return {"site_id": site_id, "mapped_tags": len(mapping.specs)}
