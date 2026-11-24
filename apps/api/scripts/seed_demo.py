"""Local development only: load the synthetic demo plant (P0-19).

    uv run python apps/api/scripts/seed_demo.py           # .\\tasks.ps1 seed
    uv run python apps/api/scripts/seed_demo.py --force   # import again even if already loaded

Generates "Riverbend Water Treatment (synthetic)": 30 days of 1-minute data for 7 tags (about 300,000
values) with a valve leak-by planted on FV-101 (driplytics_engine.demo), then imports it into alice's
Riverbend WTP site through the API, exactly like a user upload: tag mapping, direct upload to storage,
worker import. Standard library + the engine.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dev_import import import_file, request
from dev_token import PASSWORD, get_token

from driplytics_engine import demo

OUT = Path(__file__).resolve().parents[3] / ".data" / "demo"


def already_loaded() -> bool:
    token = get_token("alice", PASSWORD)
    me = request("GET", "/api/v1/me", token)
    tenant = me["memberships"][0]["tenant_id"]  # type: ignore[index]
    for site in request("GET", "/api/v1/sites", token, tenant):  # type: ignore[union-attr]
        if site["name"] != demo.SITE_NAME:  # type: ignore[index]
            continue
        imports = request("GET", f"/api/v1/sites/{site['id']}/imports", token, tenant)  # type: ignore[index]
        return any(
            i["original_filename"] == demo.EXPORT_NAME and i["status"] == "succeeded"  # type: ignore[index]
            for i in imports  # type: ignore[union-attr]
        )
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="import again even if the demo is already loaded")
    p.add_argument("--days", type=int, default=30)
    a = p.parse_args()

    if not a.force and already_loaded():
        print(f"The demo is already loaded ({demo.EXPORT_NAME} in {demo.SITE_NAME}).")
        print("Use --force to import it again.")
        return 0

    export, mapping, truth = demo.write(OUT, days=a.days)
    print(f"Generated {export.name}: {truth.rows:,} values over {a.days} days")
    leak = truth.leak_start_utc.tz_convert(demo.TZ)
    print(f"Planted: FV-101 passing ~4 gpm while closed from {leak:%b %d %H:%M %Z}")
    return import_file(export, mapping, user="alice", site_name=demo.SITE_NAME)


if __name__ == "__main__":
    sys.exit(main())
