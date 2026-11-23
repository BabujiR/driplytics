"""Local development only: sign in to the local Keycloak as a test user and call the API.

    uv run python apps/api/scripts/dev_token.py alice            # print an access token
    uv run python apps/api/scripts/dev_token.py alice --me       # ... and call GET /api/v1/me
    uv run python apps/api/scripts/dev_token.py bob --tenant     # ... and GET /api/v1/tenants/current

Uses the Keycloak "direct access grant" that the local realm enables for testing. The web app
will use the normal browser redirect flow instead. Standard library only.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KEYCLOAK = "http://localhost:8080/realms/driplytics/protocol/openid-connect/token"
API = "http://localhost:8000"
CLIENT_ID, CLIENT_SECRET = "driplytics-web", "driplytics-web-dev-secret"  # local realm only
PASSWORD = "Passw0rd!dev"  # local test users only  # noqa: S105


def get_token(user: str, password: str, wait_s: float = 90) -> str:
    """Password grant against the local realm. Keycloak takes ~30 s to start after a (re)create and
    drops connections meanwhile, so retry until `wait_s` runs out. Wrong passwords fail at once."""
    data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": user,
            "password": password,
            "scope": "openid email profile",
        }
    ).encode()
    deadline, said = time.monotonic() + wait_s, False
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(KEYCLOAK, data=data), timeout=10) as r:
                return str(json.load(r)["access_token"])
        except urllib.error.HTTPError as e:
            if e.code not in (502, 503, 504) or time.monotonic() > deadline:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if time.monotonic() > deadline:
                raise
        if not said:
            print("Waiting for Keycloak to finish starting...", file=sys.stderr, flush=True)
            said = True
        time.sleep(3)


def call(path: str, token: str, tenant: str | None = None) -> object:
    headers = {"Authorization": f"Bearer {token}"}
    if tenant:
        headers["X-Tenant-Id"] = tenant
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": json.loads(e.read() or b"{}")}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("user", choices=["alice", "bob"])
    p.add_argument("--password", default=PASSWORD)
    p.add_argument("--me", action="store_true", help="call GET /api/v1/me")
    p.add_argument(
        "--tenant", action="store_true", help="call GET /api/v1/tenants/current for your first org"
    )
    a = p.parse_args()
    try:
        token = get_token(a.user, a.password)
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        print(f"Could not reach Keycloak at {KEYCLOAK}: {e}. Is the stack running (.\\tasks.ps1 dev)?")
        return 1
    if not (a.me or a.tenant):
        print(token)
        return 0
    me = call("/api/v1/me", token)
    print(json.dumps(me, indent=2, default=str))
    if a.tenant and isinstance(me, dict) and me.get("memberships"):
        tenant_id = me["memberships"][0]["tenant_id"]
        print(json.dumps(call("/api/v1/tenants/current", token, tenant_id), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
