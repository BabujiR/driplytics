"""Input validation and API/engine contract checks (no database needed)."""

from dataclasses import MISSING, fields

import pytest
from pydantic import ValidationError

from driplytics_api.schemas import ExportLayoutModel, ImportCreate, SiteCreate, SiteUpdate, safe_filename
from driplytics_engine import ExportLayout


def test_export_layout_model_matches_engine_dataclass() -> None:
    """If the engine's ExportLayout changes, the API model must change with it."""
    engine = {f.name: f.default for f in fields(ExportLayout)}
    api = {name: f.default for name, f in ExportLayoutModel.model_fields.items()}
    assert set(engine) == set(api)
    for name, default in engine.items():
        if default is not MISSING:
            assert api[name] == default, f"default differs for {name}"


def test_layout_round_trips_into_the_engine() -> None:
    layout = ExportLayoutModel(format="wide", quality_suffix=" Quality", skiprows=3)
    assert ExportLayout(**layout.model_dump()).quality_suffix == " Quality"


def test_layout_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ExportLayoutModel.model_validate({"format": "long", "colour": "blue"})


@pytest.mark.parametrize("tz", ["America/New_York", "UTC", "Europe/Berlin"])
def test_valid_timezones(tz: str) -> None:
    assert SiteCreate(name="Plant", timezone=tz).timezone == tz


@pytest.mark.parametrize("tz", ["EST5EDT-ish", "Mars/Olympus", ""])
def test_invalid_timezones(tz: str) -> None:
    with pytest.raises(ValidationError):
        SiteCreate(name="Plant", timezone=tz)
    with pytest.raises(ValidationError):
        SiteUpdate(timezone=tz)


def test_import_create_file_types_and_size() -> None:
    assert ImportCreate(filename="export.CSV", size_bytes=10).filename == "export.CSV"
    for bad in ("export.xlsx", "malware.exe", "noext"):
        with pytest.raises(ValidationError):
            ImportCreate(filename=bad, size_bytes=10)
    with pytest.raises(ValidationError):
        ImportCreate(filename="x.csv", size_bytes=0)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("historian_long.csv", "historian_long.csv"),
        ("C:\\Users\\me\\Desktop\\PI export (Nov).csv", "PI_export_Nov_.csv"),
        ("../../etc/passwd.csv", "passwd.csv"),
        ("....csv", "csv"),
    ],
)
def test_safe_filename(name: str, expected: str) -> None:
    assert safe_filename(name) == expected
