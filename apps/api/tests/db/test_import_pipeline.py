"""P0-11 + P0-12 end to end: create import -> upload -> start -> worker job -> report.

Storage is a local folder (storage_protocol="file") and the job queue is captured, then the real
worker job runs against the same test database. This is the Phase 0 exit demo as a test.
"""

import csv
import io
import shutil
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from driplytics_api.settings import Settings
from driplytics_worker.import_job import run_import
from driplytics_worker.settings import WorkerConfig

from .conftest import TENANT_A, TENANT_B
from .helpers import FakeQueue, auth, make_app

pytestmark = pytest.mark.db
FIXTURES = Path(__file__).resolve().parents[4] / "engine" / "tests" / "fixtures" / "data"
ALICE = auth("kc-alice", "alice@a.test", TENANT_A)
BOB = auth("kc-bob", "bob@b.test", TENANT_B)


@pytest.fixture
def env(seeded, short_tmp) -> Iterator[tuple[TestClient, FakeQueue, WorkerConfig]]:
    raw, data = short_tmp / "raw", short_tmp / "data"
    settings = Settings(
        database_url=seeded.app_url, storage_protocol="file", raw_bucket=str(raw), data_bucket=str(data)
    )
    worker = WorkerConfig(
        database_url=seeded.app_url,
        storage_protocol="file",
        raw_bucket=str(raw),
        data_bucket=str(data),
        import_chunk_rows=1000,
    )
    queue = FakeQueue()
    with TestClient(make_app(settings, queue)) as c:
        yield c, queue, worker


def site_with_mapping(client: TestClient) -> str:
    site = client.post(
        "/api/v1/sites", headers=ALICE, json={"name": f"Riverbend {uuid.uuid4().hex[:6]}"}
    ).json()
    r = client.put(
        f"/api/v1/sites/{site['id']}/tag-mappings/csv",
        headers=ALICE,
        files={"file": ("tag_mapping.csv", (FIXTURES / "tag_mapping.csv").read_bytes(), "text/csv")},
    )
    assert r.status_code == 200
    return str(site["id"])


def create_and_upload(client: TestClient, site_id: str, fixture: str = "historian_long.csv") -> str:
    src = FIXTURES / fixture
    r = client.post(
        f"/api/v1/sites/{site_id}/imports",
        headers=ALICE,
        json={"filename": fixture, "size_bytes": src.stat().st_size},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["import"]["status"] == "pending" and body["upload"]["method"] == "PUT"
    dest = Path(body["upload"]["url"])  # local "bucket" in tests; a presigned URL in real life
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)
    return str(body["import"]["id"])


def test_upload_to_report_end_to_end(env) -> None:
    client, queue, worker = env
    site_id = site_with_mapping(client)
    import_id = create_and_upload(client, site_id)

    r = client.post(f"/api/v1/imports/{import_id}/start", headers=ALICE)
    assert r.status_code == 202 and r.json()["status"] == "queued"
    assert queue.jobs == [(uuid.UUID(import_id), TENANT_A)]

    result = run_import(worker, *queue.jobs[0])  # what the Arq worker does
    assert result["status"] == "succeeded"

    imp = client.get(f"/api/v1/imports/{import_id}", headers=ALICE).json()
    assert imp["status"] == "succeeded" and imp["progress"] == 1
    s = imp["summary"]
    # the Phase 0 exit demo: every value accounted for
    assert (s["total_values"], s["accepted"], s["rejected"], s["duplicates"]) == (5179, 5157, 19, 3)
    assert s["scoring_allowed"] is False  # the planted unmapped tag blocks scoring

    report = client.get(f"/api/v1/imports/{import_id}/report", headers=ALICE).json()
    assert report["unmapped_tags"] == {"XV-999.PV": 3}
    assert report["dst"]["nonexistent_local_time"] == 3

    examples = client.get(f"/api/v1/imports/{import_id}/rejected-examples.csv", headers=ALICE)
    rows = list(csv.DictReader(io.StringIO(examples.text)))
    assert {r["reason"] for r in rows} >= {"unmapped_tag", "bad_quality", "unparseable_timestamp"}

    tags = client.get(f"/api/v1/sites/{site_id}/tag-mappings", headers=ALICE).json()
    unmapped = [t["raw_tag"] for t in tags if t["role"] is None]
    assert unmapped == ["XV-999.PV"]  # seen in the file, waiting to be mapped

    values_dir = Path(
        worker.data_bucket, f"tenant={TENANT_A}", f"site={site_id}", "imports", import_id, "values"
    )
    assert len(list(values_dir.iterdir())) == 6  # one clean file per mapped tag

    actions = [
        e["action"]
        for e in client.get("/api/v1/audit", headers=ALICE, params={"entity_id": import_id}).json()
    ]
    assert actions == ["import.succeed", "import.queue", "import.create"]


def test_start_before_upload_is_409(env) -> None:
    client, queue, _ = env
    site_id = site_with_mapping(client)
    r = client.post(
        f"/api/v1/sites/{site_id}/imports", headers=ALICE, json={"filename": "later.csv", "size_bytes": 100}
    )
    r = client.post(f"/api/v1/imports/{r.json()['import']['id']}/start", headers=ALICE)
    assert r.status_code == 409 and "not been uploaded" in r.json()["detail"] and queue.jobs == []


def test_finished_import_cannot_be_started_again_and_duplicate_jobs_are_ignored(env) -> None:
    client, queue, worker = env
    import_id = create_and_upload(client, site_with_mapping(client))
    client.post(f"/api/v1/imports/{import_id}/start", headers=ALICE)
    assert run_import(worker, *queue.jobs[0])["status"] == "succeeded"
    assert run_import(worker, *queue.jobs[0])["status"] == "skipped"  # same job delivered twice
    assert client.post(f"/api/v1/imports/{import_id}/start", headers=ALICE).status_code == 409


def test_broken_file_marks_import_failed_with_reason(env) -> None:
    client, queue, worker = env
    site_id = site_with_mapping(client)
    r = client.post(
        f"/api/v1/sites/{site_id}/imports",
        headers=ALICE,
        json={"filename": "broken.parquet", "size_bytes": 10},
    )
    dest = Path(r.json()["upload"]["url"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"this is not parquet")
    import_id = r.json()["import"]["id"]
    client.post(f"/api/v1/imports/{import_id}/start", headers=ALICE)
    assert run_import(worker, *queue.jobs[0])["status"] == "failed"
    imp = client.get(f"/api/v1/imports/{import_id}", headers=ALICE).json()
    assert imp["status"] == "failed" and imp["error"] and imp["summary"] is None


def test_wrong_file_type_and_too_big_are_rejected_up_front(env) -> None:
    client, _, _ = env
    site_id = site_with_mapping(client)
    assert (
        client.post(
            f"/api/v1/sites/{site_id}/imports", headers=ALICE, json={"filename": "x.xlsx", "size_bytes": 10}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/sites/{site_id}/imports",
            headers=ALICE,
            json={"filename": "x.csv", "size_bytes": 10**15},
        ).status_code
        == 413
    )


def test_other_tenant_cannot_see_or_start_import(env) -> None:
    client, _, _ = env
    import_id = create_and_upload(client, site_with_mapping(client))
    assert client.get(f"/api/v1/imports/{import_id}", headers=BOB).status_code == 404
    assert client.post(f"/api/v1/imports/{import_id}/start", headers=BOB).status_code == 403  # viewer role
