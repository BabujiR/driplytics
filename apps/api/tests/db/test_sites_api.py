"""P0-09 + P0-10 through the real routes and database: sites, export profiles, mappings, audit."""

import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from driplytics_api.settings import Settings

from .conftest import TENANT_A, TENANT_B
from .helpers import FakeQueue, auth, make_app

pytestmark = pytest.mark.db
FIXTURES = Path(__file__).resolve().parents[4] / "engine" / "tests" / "fixtures" / "data"
ALICE = auth("kc-alice", "alice@a.test", TENANT_A)  # owner of A
BOB = auth("kc-bob", "bob@b.test", TENANT_B)  # viewer of B


@pytest.fixture
def client(seeded, short_tmp) -> Iterator[TestClient]:
    settings = Settings(
        database_url=seeded.app_url,
        storage_protocol="file",
        raw_bucket=str(short_tmp / "raw"),
        data_bucket=str(short_tmp / "data"),
    )
    with TestClient(make_app(settings, FakeQueue())) as c:
        yield c


def new_site(client: TestClient, **extra) -> dict:  # type: ignore[no-untyped-def]
    r = client.post("/api/v1/sites", headers=ALICE, json={"name": f"Plant {uuid.uuid4().hex[:6]}", **extra})
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- sites
def test_create_list_update_delete_site(client: TestClient) -> None:
    site = new_site(client, timezone="America/Chicago", display_units="si")
    assert site["timezone"] == "America/Chicago" and site["display_units"] == "si"
    assert site["id"] in {s["id"] for s in client.get("/api/v1/sites", headers=ALICE).json()}

    r = client.patch(f"/api/v1/sites/{site['id']}", headers=ALICE, json={"name": site["name"] + " North"})
    assert r.status_code == 200 and r.json()["name"].endswith(" North")

    assert client.delete(f"/api/v1/sites/{site['id']}", headers=ALICE).status_code == 204
    assert client.get(f"/api/v1/sites/{site['id']}", headers=ALICE).status_code == 404


def test_duplicate_site_name_is_409(client: TestClient) -> None:
    site = new_site(client)
    r = client.post("/api/v1/sites", headers=ALICE, json={"name": site["name"]})
    assert r.status_code == 409


def test_invalid_input_is_422(client: TestClient) -> None:
    assert (
        client.post("/api/v1/sites", headers=ALICE, json={"name": "X", "timezone": "Mars/Base"}).status_code
        == 422
    )
    assert client.post("/api/v1/sites", headers=ALICE, json={"name": "X", "colour": "red"}).status_code == 422


def test_viewer_can_read_but_not_write(client: TestClient) -> None:
    assert client.get("/api/v1/sites", headers=BOB).status_code == 200
    assert client.post("/api/v1/sites", headers=BOB, json={"name": "Nope"}).status_code == 403


def test_other_tenants_site_is_404_not_403(client: TestClient) -> None:
    site = new_site(client)
    for method in ("get", "patch", "delete"):
        kwargs = {"json": {"name": "x"}} if method == "patch" else {}
        r = getattr(client, method)(f"/api/v1/sites/{site['id']}", headers=BOB, **kwargs)
        assert r.status_code in (403, 404)  # viewer: 403 on writes by role; reads hidden by RLS -> 404
    assert client.get(f"/api/v1/sites/{site['id']}", headers=BOB).status_code == 404


# ---------------------------------------------------------------- export profiles
def test_export_profiles(client: TestClient) -> None:
    site = new_site(client)
    r = client.post(
        f"/api/v1/sites/{site['id']}/export-profiles",
        headers=ALICE,
        json={"name": "PI wide", "layout": {"format": "wide", "quality_suffix": " Quality"}},
    )
    assert r.status_code == 201 and r.json()["layout"]["quality_suffix"] == " Quality"
    pid = r.json()["id"]
    r = client.patch(f"/api/v1/export-profiles/{pid}", headers=ALICE, json={"layout": {"format": "long"}})
    assert r.status_code == 200 and r.json()["layout"]["format"] == "long"
    bad = client.post(
        f"/api/v1/sites/{site['id']}/export-profiles",
        headers=ALICE,
        json={"name": "Bad", "layout": {"format": "sideways"}},
    )
    assert bad.status_code == 422
    assert len(client.get(f"/api/v1/sites/{site['id']}/export-profiles", headers=ALICE).json()) == 1


# ---------------------------------------------------------------- tag mappings
def test_tag_mapping_csv_upload_and_reupload(client: TestClient) -> None:
    site = new_site(client)
    csv_bytes = (FIXTURES / "tag_mapping.csv").read_bytes()
    for _ in range(2):  # second upload updates in place
        r = client.put(
            f"/api/v1/sites/{site['id']}/tag-mappings/csv",
            headers=ALICE,
            files={"file": ("tag_mapping.csv", csv_bytes, "text/csv")},
        )
        assert r.status_code == 200 and r.json()["mapped_tags"] == 6
    rows = client.get(f"/api/v1/sites/{site['id']}/tag-mappings", headers=ALICE).json()
    assert len(rows) == 6 and {r["role"] for r in rows} >= {"flow", "valve_state", "pump_state"}


def test_invalid_mapping_csv_lists_every_problem(client: TestClient) -> None:
    site = new_site(client)
    bad = b"raw_tag,canonical_tag,role,source_unit,target_unit\nA,a,flow,gpm,psi\nB,b,valve_state,,\n"
    r = client.put(
        f"/api/v1/sites/{site['id']}/tag-mappings/csv",
        headers=ALICE,
        files={"file": ("bad.csv", bad, "text/csv")},
    )
    assert r.status_code == 422 and "line 2" in r.json()["detail"] and "line 3" in r.json()["detail"]
    assert client.get(f"/api/v1/sites/{site['id']}/tag-mappings", headers=ALICE).json() == []  # nothing saved


# ---------------------------------------------------------------- audit (P0-09)
def test_changes_are_audited_and_admin_only(client: TestClient) -> None:
    site = new_site(client)
    client.patch(f"/api/v1/sites/{site['id']}", headers=ALICE, json={"display_units": "si"})
    events = client.get(
        "/api/v1/audit", headers=ALICE, params={"entity_type": "site", "entity_id": site["id"]}
    ).json()
    assert [e["action"] for e in events] == ["site.update", "site.create"]  # newest first
    assert events[0]["before"]["display_units"] == "us" and events[0]["after"]["display_units"] == "si"
    assert events[0]["user_email"] == "alice@a.test"
    assert client.get("/api/v1/audit", headers=BOB).status_code == 403  # viewer
