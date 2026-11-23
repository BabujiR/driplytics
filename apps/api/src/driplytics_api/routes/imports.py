"""Upload flow (P0-11): create an import + upload URL, upload straight to storage, start, follow progress.

1. POST /sites/{site_id}/imports        -> import (status 'pending') + presigned PUT URL
2. PUT  <upload.url>  (browser -> bucket, the file never passes through the API)
3. POST /imports/{id}/start              -> verifies the object, status 'queued', enqueues the job
4. GET  /imports/{id}                    -> status + progress (0..1) while the worker runs
5. GET  /imports/{id}/report             -> the full import report once 'succeeded'
"""

import csv
import io
import uuid
from contextlib import AbstractContextManager
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from starlette.concurrency import run_in_threadpool

from driplytics_api import audit
from driplytics_api.auth.deps import TenantContext, require_role
from driplytics_api.auth.roles import Role
from driplytics_api.db.connection import Conn, request_tx
from driplytics_api.queue import JobQueue, get_queue
from driplytics_api.responses import (
    COMMON_ERRORS,
    ErrorOut,
    ImportCreatedOut,
    ImportDetailOut,
    ImportOut,
    ImportReportOut,
)
from driplytics_api.schemas import ImportCreate, safe_filename
from driplytics_api.settings import Settings, get_settings
from driplytics_api.storage import object_size, presign_put

router = APIRouter(prefix="/api/v1", tags=["imports"], responses=COMMON_ERRORS)

Viewer = Annotated[TenantContext, Depends(require_role(Role.VIEWER))]
Engineer = Annotated[TenantContext, Depends(require_role(Role.ENGINEER))]
SettingsDep = Annotated[Settings, Depends(get_settings)]

IMPORT_COLS = (
    "id, site_id, export_profile_id, source, object_key, original_filename, size_bytes, status, progress, "
    "error, created_by, created_at, started_at, finished_at"
)
STARTABLE = ("pending", "queued", "failed")


def _tx(settings: Settings, ctx: TenantContext) -> AbstractContextManager[Conn]:
    return request_tx(settings.database_url, user_id=ctx.principal.user_id, tenant_id=ctx.tenant_id)


def _get_import(conn: Conn, import_id: UUID, *, lock: bool = False) -> dict[str, Any]:
    row = conn.execute(
        f"SELECT {IMPORT_COLS} FROM data_import WHERE id = %s" + (" FOR UPDATE" if lock else ""),
        (import_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "import not found")
    return row


@router.post(
    "/sites/{site_id}/imports",
    status_code=status.HTTP_201_CREATED,
    response_model=ImportCreatedOut,
    responses={413: {"model": ErrorOut, "description": "File too large"}},
)
def create_import(site_id: UUID, body: ImportCreate, ctx: Engineer, settings: SettingsDep) -> dict[str, Any]:
    if body.size_bytes > settings.max_upload_bytes:
        raise HTTPException(
            413,
            f"files up to {settings.max_upload_bytes // 1024**3} GB are supported",
        )
    import_id = uuid.uuid4()
    key = f"tenant={ctx.tenant_id}/site={site_id}/imports/{import_id}/{safe_filename(body.filename)}"
    with _tx(settings, ctx) as conn:
        if conn.execute("SELECT 1 FROM site WHERE id = %s", (site_id,)).fetchone() is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "site not found")
        if (
            body.export_profile_id is not None
            and conn.execute(
                "SELECT 1 FROM export_profile WHERE id = %s AND site_id = %s",
                (body.export_profile_id, site_id),
            ).fetchone()
            is None
        ):
            raise HTTPException(422, "export profile does not belong to this site")
        row = conn.execute(
            f"INSERT INTO data_import (id, tenant_id, site_id, export_profile_id, source, object_key, "
            f"original_filename, size_bytes, status, created_by) "
            f"VALUES (%s, %s, %s, %s, 'upload', %s, %s, %s, 'pending', %s) RETURNING {IMPORT_COLS}",
            (
                import_id,
                ctx.tenant_id,
                site_id,
                body.export_profile_id,
                key,
                body.filename,
                body.size_bytes,
                ctx.principal.user_id,
            ),
        ).fetchone()
        assert row is not None
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="import.create",
            entity_type="import",
            entity_id=import_id,
            after=row,
        )
    return {"import": row, "upload": presign_put(settings, settings.raw_bucket, key)}


def _mark_queued(settings: Settings, ctx: TenantContext, import_id: UUID) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        imp = _get_import(conn, import_id, lock=True)
        if imp["status"] not in STARTABLE:
            raise HTTPException(status.HTTP_409_CONFLICT, f"import is already {imp['status']}")
        size = object_size(settings, settings.raw_bucket, imp["object_key"])
        if size is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "the file has not been uploaded yet")
        if size > settings.max_upload_bytes:
            raise HTTPException(413, "uploaded file is too large")
        row = conn.execute(
            f"UPDATE data_import SET status = 'queued', size_bytes = %s, progress = 0, error = NULL "
            f"WHERE id = %s RETURNING {IMPORT_COLS}",
            (size, import_id),
        ).fetchone()
        assert row is not None
        audit.record(
            conn,
            tenant_id=ctx.tenant_id,
            user_id=ctx.principal.user_id,
            action="import.queue",
            entity_type="import",
            entity_id=import_id,
            before={"status": imp["status"]},
            after={"status": "queued", "size_bytes": size},
        )
        return row


@router.post(
    "/imports/{import_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ImportOut,
    responses={
        409: {"model": ErrorOut, "description": "Not uploaded yet, or already started"},
        413: {"model": ErrorOut, "description": "Uploaded file too large"},
        503: {"model": ErrorOut, "description": "Job queue unavailable; call start again"},
    },
)
async def start_import(
    import_id: UUID, ctx: Engineer, settings: SettingsDep, queue: Annotated[JobQueue, Depends(get_queue)]
) -> dict[str, Any]:
    row = await run_in_threadpool(_mark_queued, settings, ctx, import_id)
    try:
        await queue.enqueue_import(import_id, ctx.tenant_id)
    except Exception as exc:  # status stays 'queued'; calling start again retries the enqueue
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "job queue unavailable, try again") from exc
    return row


@router.get("/sites/{site_id}/imports", response_model=list[ImportOut])
def list_imports(site_id: UUID, ctx: Viewer, settings: SettingsDep) -> list[dict[str, Any]]:
    with _tx(settings, ctx) as conn:
        return conn.execute(
            f"SELECT {IMPORT_COLS} FROM data_import WHERE site_id = %s ORDER BY created_at DESC LIMIT 50",
            (site_id,),
        ).fetchall()


@router.get("/imports/{import_id}", response_model=ImportDetailOut)
def get_import(import_id: UUID, ctx: Viewer, settings: SettingsDep) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        imp = _get_import(conn, import_id)
        summary = conn.execute(
            "SELECT total_values, accepted, rejected, duplicates, rejected_by_reason, scoring_allowed "
            "FROM import_report WHERE import_id = %s",
            (import_id,),
        ).fetchone()
    return {**imp, "summary": summary}


@router.get("/imports/{import_id}/report", response_model=ImportReportOut)
def get_import_report(import_id: UUID, ctx: Viewer, settings: SettingsDep) -> dict[str, Any]:
    with _tx(settings, ctx) as conn:
        _get_import(conn, import_id)
        row = conn.execute("SELECT report FROM import_report WHERE import_id = %s", (import_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not ready yet")
    report: dict[str, Any] = row["report"]
    return report


@router.get(
    "/imports/{import_id}/rejected-examples.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}, "description": "CSV file"}},
)
def download_rejected_examples(import_id: UUID, ctx: Viewer, settings: SettingsDep) -> Response:
    """Up to 20 example rows per rejection reason (the full rejected-row export comes later)."""
    report = get_import_report(import_id, ctx, settings)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["reason", "seq", "raw_tag", "timestamp", "value"])
    for reason, rows in sorted(report.get("rejected_examples", {}).items()):
        for r in rows:
            w.writerow([reason, r.get("seq"), r.get("raw_tag"), r.get("timestamp"), r.get("value")])
    return Response(
        out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="rejected-{import_id}.csv"'},
    )
