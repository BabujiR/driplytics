"""Write the API's OpenAPI document to packages/contracts/openapi.json (P0-13).

    uv run python apps/api/scripts/export_openapi.py           # write the file
    uv run python apps/api/scripts/export_openapi.py --check   # exit 1 if the committed file is stale

The TypeScript client in packages/contracts is generated from this file
(`pnpm --filter @driplytics/contracts generate`, or `.\\tasks.ps1 contracts` for both steps).
A test (apps/api/tests/test_openapi_contract.py) fails whenever the API and this file disagree.
"""

import argparse
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.json"


def render() -> str:
    from driplytics_api.main import app

    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="fail if the committed file is out of date")
    a = p.parse_args()
    text = render()
    current = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else None
    if a.check:
        if current != text:
            print(f"{OUT} is out of date. Run: .\\tasks.ps1 contracts", file=sys.stderr)
            return 1
        print("openapi.json is up to date")
        return 0
    if current == text:
        print(f"unchanged: {OUT}")
    else:
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
