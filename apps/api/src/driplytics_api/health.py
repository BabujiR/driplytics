"""Dependency checks behind /health/ready. Each returns (ok, detail) and never raises."""

from collections.abc import Callable
from dataclasses import dataclass

import fsspec
import psycopg
import redis

from .settings import Settings


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    detail: str


def check_postgres(s: Settings) -> CheckResult:
    try:
        with psycopg.connect(s.database_url, connect_timeout=int(s.readiness_timeout_s)) as conn:
            version = conn.execute("SHOW server_version").fetchone()
        return CheckResult(True, f"postgres {version[0] if version else '?'}")
    except Exception as exc:
        return CheckResult(False, f"{type(exc).__name__}: {exc}"[:300])


def check_redis(s: Settings) -> CheckResult:
    try:
        client = redis.Redis.from_url(s.redis_url, socket_timeout=s.readiness_timeout_s)
        client.ping()
        return CheckResult(True, "redis ping ok")
    except Exception as exc:
        return CheckResult(False, f"{type(exc).__name__}: {exc}"[:300])


def check_storage(s: Settings) -> CheckResult:
    try:
        opts: dict[str, object] = {}
        if s.storage_protocol == "s3":
            opts = {"key": s.storage_key, "secret": s.storage_secret}
            if s.storage_endpoint_url:
                opts["client_kwargs"] = {"endpoint_url": s.storage_endpoint_url}
        fs = fsspec.filesystem(s.storage_protocol, **opts)
        missing = [b for b in (s.raw_bucket, s.data_bucket) if not fs.exists(b)]
        created: list[str] = []
        if missing and s.storage_auto_create_buckets:
            for bucket in missing:
                fs.mkdir(bucket)
                created.append(bucket)
            fs.invalidate_cache()
            missing = [b for b in missing if not fs.exists(b)]
        if missing:
            return CheckResult(False, f"missing buckets: {', '.join(missing)}")
        note = f" (created {', '.join(created)})" if created else ""
        return CheckResult(True, f"{s.storage_protocol} buckets ok{note}")
    except Exception as exc:
        return CheckResult(False, f"{type(exc).__name__}: {exc}"[:300])


CHECKS: dict[str, Callable[[Settings], CheckResult]] = {
    "postgres": check_postgres,
    "redis": check_redis,
    "storage": check_storage,
}
