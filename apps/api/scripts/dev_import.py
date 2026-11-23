"""Local development only: the Phase 0 exit demo against the running stack.

    uv run python apps/api/scripts/dev_import.py              # uses the engine's synthetic fixtures
    uv run python apps/api/scripts/dev_import.py my_export.csv --mapping my_tags.csv

Signs in as alice (Keycloak), picks her first site (Riverbend WTP), uploads the tag mapping,
creates an import, uploads the file straight to object storage with the presigned URL, starts the
import, follows progress, and prints the report summary. Standard library only.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dev_token import API, PASSWORD, get_token

FIXTURES = Path(__file__).resolve().parents[3] / "engine" / "tests" / "fixtures" / "data"


def request(
    method: str,
    path: str,
    token: str,
    tenant: str | None = None,
    body: object = None,
    raw: bytes | None = None,
    content_type: str | None = None,
) -> object:
    headers = {"Authorization": f"Bearer {token}"}
    if tenant:
        headers["X-Tenant-Id"] = tenant
    data = raw
    if body is not None:
        data, content_type = json.dumps(body).encode(), "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')}")


def multipart(field: str, filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    body = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
            f"Content-Type: text/csv\r\n\r\n"
        ).encode()
        + content
        + f"\r\n--{boundary}--\r\n".encode()
    )
    return body, f"multipart/form-data; boundary={boundary}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?", default=str(FIXTURES / "historian_long.csv"))
    p.add_argument("--mapping", default=str(FIXTURES / "tag_mapping.csv"))
    a = p.parse_args()
    export, mapping = Path(a.file), Path(a.mapping)

    token = get_token("alice", PASSWORD)
    me = request("GET", "/api/v1/me", token)
    tenant = me["memberships"][0]["tenant_id"]  # type: ignore[index]
    sites = request("GET", "/api/v1/sites", token, tenant)
    site = sites[0]  # type: ignore[index]
    print(f"Signed in as alice -> {me['memberships'][0]['name']} / site '{site['name']}'")  # type: ignore[index]

    body, ctype = multipart("file", mapping.name, mapping.read_bytes())
    r = request(
        "PUT", f"/api/v1/sites/{site['id']}/tag-mappings/csv", token, tenant, raw=body, content_type=ctype
    )
    print(f"Tag mapping uploaded: {r['mapped_tags']} tags")  # type: ignore[index]

    created = request(
        "POST",
        f"/api/v1/sites/{site['id']}/imports",
        token,
        tenant,
        body={"filename": export.name, "size_bytes": export.stat().st_size},
    )
    imp, upload = created["import"], created["upload"]  # type: ignore[index]
    put = urllib.request.Request(upload["url"], data=export.read_bytes(), method="PUT")
    with urllib.request.urlopen(put, timeout=300) as resp:
        size = export.stat().st_size
        print(f"Uploaded {export.name} ({size:,} bytes) straight to storage: HTTP {resp.status}")

    request("POST", f"/api/v1/imports/{imp['id']}/start", token, tenant)
    print("Import queued; waiting for the worker", end="", flush=True)
    for _ in range(600):
        cur = request("GET", f"/api/v1/imports/{imp['id']}", token, tenant)
        if cur["status"] in ("succeeded", "failed"):  # type: ignore[index]
            break
        print(f" {int(cur['progress'] * 100)}%", end="", flush=True)  # type: ignore[index]
        time.sleep(1)
    print()
    if cur["status"] != "succeeded":  # type: ignore[index]
        print("Import FAILED:", cur["error"])  # type: ignore[index]
        return 1
    s = cur["summary"]  # type: ignore[index]
    print(
        f"Every value accounted for: {s['total_values']:,} = {s['accepted']:,} accepted "
        f"+ {s['rejected']:,} rejected + {s['duplicates']:,} duplicates"
    )
    for reason, n in sorted(s["rejected_by_reason"].items(), key=lambda kv: -kv[1]):
        if n:
            print(f"  rejected {reason}: {n}")
    print("Scoring:", "ALLOWED" if s["scoring_allowed"] else "BLOCKED (map the unmapped tags)")
    print(f"Full report: {API}/api/v1/imports/{imp['id']}/report  (needs the bearer token)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
