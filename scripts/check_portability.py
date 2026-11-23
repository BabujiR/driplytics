"""P0-24 / ADR 0007: keep application code cloud-portable (GCP now, AWS later).

Fails if application code imports a cloud vendor SDK directly. Cloud access must go through the
portable layers: fsspec (storage), botocore S3 presigning in apps/api/.../storage.py, environment
variables for configuration, OpenTelemetry for observability.

    uv run python scripts/check_portability.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIRS = ["apps/api/src", "services/worker/src", "engine/src"]
FORBIDDEN = [
    (re.compile(r"^\s*(from|import)\s+google\.cloud\b"), "google.cloud SDK (use fsspec / env config)"),
    (re.compile(r"^\s*(from|import)\s+google\.api_core\b"), "google.api_core"),
    (re.compile(r"^\s*(from|import)\s+boto3\b"), "boto3 (use fsspec; presigning lives in storage.py)"),
    (re.compile(r"^\s*(from|import)\s+(azure|aiobotocore)\b"), "vendor SDK"),
]
ALLOWED = {"apps/api/src/driplytics_api/storage.py"}  # the one place allowed to sign S3 URLs


def main() -> int:
    problems = []
    for d in APP_DIRS:
        for path in sorted((ROOT / d).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel in ALLOWED:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for pattern, why in FORBIDDEN:
                    if pattern.search(line):
                        problems.append(f"{rel}:{n}: {why}: {line.strip()}")
    if problems:
        print("Cloud-portability check failed (ADR 0007):\n  " + "\n  ".join(problems))
        return 1
    print(f"portability ok ({', '.join(APP_DIRS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
