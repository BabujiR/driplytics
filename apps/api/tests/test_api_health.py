import pytest
from fastapi.testclient import TestClient

from driplytics_api import health, main
from driplytics_api.health import CheckResult
from driplytics_api.settings import Settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.app)


def test_live(client: TestClient) -> None:
    r = client.get("/health/live")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_ready_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "CHECKS", {"x": lambda s: CheckResult(True, "fine")})
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["checks"]["x"] == {"ok": True, "detail": "fine"}


def test_ready_reports_503_when_a_dependency_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    checks = {"db": lambda s: CheckResult(True, "ok"), "redis": lambda s: CheckResult(False, "refused")}
    monkeypatch.setattr(main, "CHECKS", checks)
    r = client.get("/health/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "degraded" and r.json()["checks"]["redis"]["ok"] is False


def test_version(client: TestClient) -> None:
    assert client.get("/api/v1/version").json()["service"] == "driplytics-api"


def test_openapi_is_served(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200


class FakeFS:
    """Minimal stand-in for an fsspec filesystem."""

    def __init__(self, buckets: set[str]) -> None:
        self.buckets = set(buckets)
        self.made: list[str] = []

    def exists(self, path: str) -> bool:
        return path in self.buckets

    def mkdir(self, path: str) -> None:
        self.buckets.add(path)
        self.made.append(path)

    def invalidate_cache(self) -> None:
        pass


def test_storage_reports_missing_buckets_when_auto_create_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    fs = FakeFS({"driplytics-raw"})
    monkeypatch.setattr(health.fsspec, "filesystem", lambda *a, **k: fs)
    r = health.check_storage(Settings(storage_auto_create_buckets=False))
    assert not r.ok and "driplytics-data" in r.detail and fs.made == []


def test_storage_creates_missing_buckets_in_local_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    fs = FakeFS(set())
    monkeypatch.setattr(health.fsspec, "filesystem", lambda *a, **k: fs)
    r = health.check_storage(Settings(storage_auto_create_buckets=True))
    assert r.ok and "created" in r.detail
    assert fs.made == ["driplytics-raw", "driplytics-data"]
