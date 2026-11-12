"""Keep intentional starter placeholders and their generated test stubs in step (#498).

``TODO: implement {{ route_name }}`` is the user-facing response body of a generated HTTP handler,
not a developer TODO. The generated test asserts on the same string, so the pair must change
together; a one-sided edit would ship a generated project whose own test fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TEMPLATES = (
    Path(__file__).resolve().parent.parent / "src" / "azure_functions_scaffold" / "templates"
)
PLACEHOLDER = "TODO: implement {{ route_name }}"

PAIRS = (
    ("partials/functions/http_module.py.j2", "partials/functions/http_test.py.j2"),
    ("partials/route_blueprint.py.j2", "partials/route_test.py.j2"),
)


@pytest.mark.parametrize(("module", "stub"), PAIRS)
def test_starter_placeholder_matches_generated_test_stub(module: str, stub: str) -> None:
    module_text = (TEMPLATES / module).read_text(encoding="utf-8")
    stub_text = (TEMPLATES / stub).read_text(encoding="utf-8")

    assert f'body="{PLACEHOLDER}"' in module_text
    assert f'b"{PLACEHOLDER}"' in stub_text
