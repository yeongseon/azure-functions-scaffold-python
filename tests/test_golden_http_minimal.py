"""Golden-file snapshot of a minimal generated HTTP project (#477).

Existing tests pin the file *counts* and dependency sets of the HTTP starters
(``test_simple_http_starter_contract.py``) and import a strict project's handlers
(``test_generated_http_indexing.py``). None of them pins the exact generated paths and file
contents of the lightest HTTP project, ``--preset minimal`` with no OpenAPI, validation, Doctor,
GitHub Actions or git, so an unintended template change to it passes every existing test.

The snapshot lives in ``tests/fixtures/golden_http_minimal.json``. It runs offline, needs no
Azure credentials, and stores no secret-bearing settings: ``local.settings.json.example`` is
snapshotted by path only.

Review and refresh after an intentional template change::

    UPDATE_GOLDEN=1 pytest tests/test_golden_http_minimal.py --no-cov
    git diff tests/fixtures/golden_http_minimal.json   # review every changed line

then run ``pytest tests/test_golden_http_minimal.py`` without the variable to confirm.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "golden_http_minimal.json"
PROJECT_NAME = "golden-http"
TMP_PLACEHOLDER = "<TMP>"
# Snapshotted by path only so the fixture never carries settings values.
PATH_ONLY = frozenset({"local.settings.json.example"})


def _generate(tmp_path: Path) -> Path:
    return scaffold_project(
        project_name=PROJECT_NAME,
        destination=tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="minimal",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
            include_openapi=False,
            include_validation=False,
            include_doctor=False,
        ),
    )


def _snapshot(root: Path, tmp_path: Path) -> dict[str, str | None]:
    files: dict[str, str | None] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in PATH_ONLY:
            files[relative] = None
            continue
        text = path.read_text(encoding="utf-8").replace(str(tmp_path), TMP_PLACEHOLDER)
        files[relative] = text.replace("\r\n", "\n")
    return files


def test_minimal_http_project_matches_golden_snapshot(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    actual = _snapshot(root, tmp_path)

    if os.environ.get("UPDATE_GOLDEN") == "1":
        GOLDEN.write_text(
            json.dumps({"files": actual}, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        pytest.skip("golden snapshot rewritten; review the diff and rerun without UPDATE_GOLDEN")

    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))["files"]
    assert sorted(actual) == sorted(expected), "generated path set drifted from the golden snapshot"
    drifted = [name for name in expected if actual[name] != expected[name]]
    assert drifted == [], f"content drifted from the golden snapshot: {drifted}"


def test_golden_snapshot_is_deterministic_and_normalized(tmp_path: Path) -> None:
    first = _snapshot(_generate(tmp_path / "a"), tmp_path / "a")
    second = _snapshot(_generate(tmp_path / "b"), tmp_path / "b")

    assert first == second
    assert not any(str(tmp_path) in (text or "") for text in first.values())
    assert TMP_PLACEHOLDER not in GOLDEN.read_text(encoding="utf-8")


def test_minimal_http_project_has_an_indexable_v2_http_entrypoint(tmp_path: Path) -> None:
    root = _generate(tmp_path)
    sys.path.insert(0, str(root))
    try:
        import function_app

        functions = function_app.app.get_functions()
        indexed = {
            function.get_function_name(): (
                function.get_trigger().type,
                [str(method.value) for method in getattr(function.get_trigger(), "methods", [])],
            )
            for function in functions
        }
    finally:
        sys.path.remove(str(root))
        for module_name in list(sys.modules):
            if module_name in {"app", "function_app"} or module_name.startswith("app."):
                del sys.modules[module_name]

    assert indexed == {
        "health": ("httpTrigger", ["GET"]),
        "receive_webhook": ("httpTrigger", ["POST"]),
    }
