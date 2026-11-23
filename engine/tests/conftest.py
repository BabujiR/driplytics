import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

DATA = ROOT / "tests" / "fixtures" / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    if not (DATA / "expected.json").exists():
        from generate import generate
        generate(DATA)
    return DATA


@pytest.fixture(scope="session")
def expected(data_dir) -> dict:
    return json.loads((data_dir / "expected.json").read_text())


@pytest.fixture(scope="session")
def mapping(data_dir):
    from plant_ingest import TagMapping
    return TagMapping.from_csv(data_dir / "tag_mapping.csv")
