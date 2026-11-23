"""P0-12: the import job. Uploaded file in object storage -> engine -> clean Parquet + import report.

Steps (each database step is its own short transaction, under the import's tenant):
  1. Load the import, its site's time zone, its export profile and the site's tag mappings.
     Mark it 'running' (only from 'queued': a duplicate delivery of the job is ignored).
  2. Run the engine's chunked importer straight from object storage, writing per-tag Parquet to
     <data_bucket>/tenant=<t>/site=<s>/imports/<import_id>/values/ and updating progress.
  3. Save the report (the database re-checks accepted + rejected + duplicates = total), register
     every raw tag seen in the file, mark 'succeeded', write an audit entry.
  On any error: mark 'failed' with the message and audit it. Errors are not retried automatically:
  they are usually the file or the mapping, and a user retries with POST /imports/{id}/start.
"""

import json
import logging
import time
from dataclasses import fields
from typing import Any
from uuid import UUID

import pandas as pd
from psycopg.types.json import Jsonb

from driplytics_engine import ExportLayout, ImportConfig, ImportProgress, TagMapping, import_large_file

from .db import Conn, tenant_tx
from .settings import WorkerConfig

log = logging.getLogger("driplytics.worker.import")

MAPPING_COLUMNS = [
    "raw_tag",
    "canonical_tag",
    "role",
    "source_unit",
    "target_unit",
    "is_totalizer",
    "rollover_max",
    "max_gap_s",
    "state_true",
    "state_false",
    "low_flow_cutoff",
]
_LAYOUT_FIELDS = {f.name for f in fields(ExportLayout)}


def mapping_from_rows(rows: list[dict[str, Any]]) -> TagMapping:
    """Database rows -> engine TagMapping (validated by the engine exactly like a CSV upload)."""

    def text(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)

    frame = pd.DataFrame(
        [{c: text(r.get(c)) for c in MAPPING_COLUMNS} for r in rows], columns=MAPPING_COLUMNS
    )
    return TagMapping.from_frame(frame)


def layout_from_json(layout: dict[str, Any] | None) -> ExportLayout:
    return ExportLayout(**{k: v for k, v in (layout or {}).items() if k in _LAYOUT_FIELDS})


def _audit(conn: Conn, tenant_id: UUID, action: str, import_id: UUID, after: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO audit_event (tenant_id, user_id, action, entity_type, entity_id, after) "
        "VALUES (%s, NULL, %s, 'import', %s, %s)",
        (tenant_id, action, str(import_id), Jsonb(after)),
    )


def run_import(cfg: WorkerConfig, import_id: UUID, tenant_id: UUID) -> dict[str, Any]:
    t0 = time.perf_counter()
    with tenant_tx(cfg.database_url, tenant_id) as conn:
        imp = conn.execute(
            "SELECT i.id, i.site_id, i.object_key, i.status, s.timezone, p.layout "
            "FROM data_import i JOIN site s ON s.id = i.site_id "
            "LEFT JOIN export_profile p ON p.id = i.export_profile_id WHERE i.id = %s FOR UPDATE OF i",
            (import_id,),
        ).fetchone()
        if imp is None:
            log.warning("import %s not found for tenant %s", import_id, tenant_id)
            return {"status": "missing"}
        if imp["status"] != "queued":
            log.info("import %s is %s, not queued: skipping duplicate delivery", import_id, imp["status"])
            return {"status": "skipped", "current": imp["status"]}
        rows = conn.execute(
            "SELECT t.raw_tag, m.canonical_tag, m.role, m.source_unit, m.target_unit, m.is_totalizer, "
            "m.rollover_max, m.max_gap_s, m.state_true, m.state_false, m.low_flow_cutoff "
            "FROM tag_mapping m JOIN tag t ON t.id = m.tag_id WHERE t.site_id = %s ORDER BY t.raw_tag",
            (imp["site_id"],),
        ).fetchall()
        conn.execute(
            "UPDATE data_import SET status = 'running', started_at = now(), progress = 0, error = NULL "
            "WHERE id = %s",
            (import_id,),
        )

    site_id: UUID = imp["site_id"]
    raw_url = cfg.object_url(cfg.raw_bucket, imp["object_key"])
    out_url = cfg.object_url(cfg.data_bucket, f"tenant={tenant_id}/site={site_id}/imports/{import_id}")
    last = {"t": 0.0}

    def on_progress(event: ImportProgress) -> None:
        now = time.monotonic()
        if event.fraction is None or (now - last["t"] < 2.0 and event.stage != "done"):
            return  # at most one progress write every 2 s
        last["t"] = now
        with tenant_tx(cfg.database_url, tenant_id) as c:
            c.execute(
                "UPDATE data_import SET progress = %s WHERE id = %s",
                (round(min(event.fraction, 0.99), 4), import_id),
            )

    try:
        result = import_large_file(
            raw_url,
            mapping_from_rows(rows),
            out_url,
            layout_from_json(imp["layout"]),
            ImportConfig(timezone=imp["timezone"], keep_ledger=False),
            chunksize=cfg.import_chunk_rows,
            storage_options=cfg.storage_options(),
            progress=on_progress,
        )
        report = json.loads(result.report.to_json())
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"[:2000]
        log.exception("import %s failed", import_id)
        with tenant_tx(cfg.database_url, tenant_id) as conn:
            conn.execute(
                "UPDATE data_import SET status = 'failed', error = %s, finished_at = now() WHERE id = %s",
                (message, import_id),
            )
            _audit(conn, tenant_id, "import.fail", import_id, {"error": message})
        return {"status": "failed", "error": message}

    raw_tags = sorted({t["raw_tag"] for t in report["tags"]} | set(report["unmapped_tags"]))
    with tenant_tx(cfg.database_url, tenant_id) as conn:
        conn.execute(
            "INSERT INTO import_report (import_id, tenant_id, total_values, accepted, rejected, duplicates, "
            "rejected_by_reason, examples, report, scoring_allowed) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (import_id) DO UPDATE SET total_values = EXCLUDED.total_values, "
            "accepted = EXCLUDED.accepted, rejected = EXCLUDED.rejected, duplicates = EXCLUDED.duplicates, "
            "rejected_by_reason = EXCLUDED.rejected_by_reason, examples = EXCLUDED.examples, "
            "report = EXCLUDED.report, scoring_allowed = EXCLUDED.scoring_allowed, created_at = now()",
            (
                import_id,
                tenant_id,
                report["total_values"],
                report["accepted"],
                report["rejected"],
                report["duplicates"],
                Jsonb(report["rejected_by_reason"]),
                Jsonb(report["rejected_examples"]),
                Jsonb(report),
                report["scoring_allowed"],
            ),
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO tag (tenant_id, site_id, raw_tag) VALUES (%s, %s, %s) "
                "ON CONFLICT (site_id, raw_tag) DO NOTHING",
                [(tenant_id, site_id, t) for t in raw_tags],
            )
        conn.execute(
            "UPDATE data_import SET status = 'succeeded', progress = 1, finished_at = now() WHERE id = %s",
            (import_id,),
        )
        summary = {
            k: report[k] for k in ("total_values", "accepted", "rejected", "duplicates", "scoring_allowed")
        }
        _audit(conn, tenant_id, "import.succeed", import_id, summary)
    log.info("import %s done in %.1fs: %s", import_id, time.perf_counter() - t0, summary)
    return {"status": "succeeded", **summary}
