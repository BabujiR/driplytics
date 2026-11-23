"""P0-13: the committed OpenAPI document (and so the generated TypeScript client) matches the API,
and every endpoint has a typed contract."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from driplytics_api.main import app

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_openapi.py"
spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
assert spec is not None and spec.loader is not None
export_openapi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_openapi)

DOC: dict[str, Any] = app.openapi()
OPERATIONS = [
    (path, method, op)
    for path, item in DOC["paths"].items()
    for method, op in item.items()
    if method in {"get", "post", "put", "patch", "delete"}
]


def test_committed_openapi_json_is_up_to_date() -> None:
    committed = export_openapi.OUT.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert committed == export_openapi.render(), (
        "packages/contracts/openapi.json is stale. Run: .\\tasks.ps1 contracts (then commit both files)"
    )


def test_operation_ids_are_the_route_function_names() -> None:
    ids = [op["operationId"] for _, _, op in OPERATIONS]
    assert len(ids) == len(set(ids))
    assert {"list_sites", "create_import", "start_import", "get_import_report", "me"} <= set(ids)


@pytest.mark.parametrize(("path", "method", "op"), OPERATIONS, ids=lambda v: v if isinstance(v, str) else "")
def test_every_success_response_has_a_schema(path: str, method: str, op: dict[str, Any]) -> None:
    """No untyped `{}` responses: the generated client must know what each endpoint returns."""
    for code, resp in op["responses"].items():
        if not code.startswith("2") or code == "204":
            continue
        content = resp.get("content", {})
        assert content, f"{method.upper()} {path} {code} has no content"
        for media, body in content.items():
            schema = body.get("schema", {})
            assert schema not in ({}, {"title": "Response"}), (
                f"{method.upper()} {path} {code} {media} is untyped"
            )
            assert schema.get("additionalProperties") is not True or "properties" in schema, (
                f"{method.upper()} {path} {code} returns a free-form object; add a response_model"
            )


def test_errors_are_documented() -> None:
    op = DOC["paths"]["/api/v1/sites/{site_id}"]["get"]
    assert {"401", "403", "404"} <= set(op["responses"])
    assert "ErrorOut" in json.dumps(op["responses"]["404"])


def test_create_import_response_uses_the_import_key() -> None:
    schema = DOC["components"]["schemas"]["ImportCreatedOut"]
    assert set(schema["required"]) == {"import", "upload"}
