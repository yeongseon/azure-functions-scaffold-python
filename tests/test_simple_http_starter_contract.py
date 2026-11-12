"""Pin what each way of creating a simple HTTP project generates (#454).

``docs/guide/templates.md#choosing-an-http-starter`` documents the file counts and runtime
dependencies of ``afs new`` and of the lighter ``afs advanced new`` presets. These tests generate
the same projects and compare, so the documented comparison and the generated output cannot drift
apart, and an unintended change to what ``afs new`` or ``--preset minimal`` produces fails first.
"""

from __future__ import annotations

from pathlib import Path
import re
import tomllib

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import INTENT_SPECS, build_project_options

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDE = REPO_ROOT / "docs" / "guide" / "templates.md"

# What the test-only files of the layered HTTP scaffold are, and what `minimal` omits.
GENERATED_TESTS = {"tests/test_health.py", "tests/test_webhooks.py"}
BASE_RUNTIME = {"azure-functions", "azure-functions-logging", "orjson"}
API_EXTRAS = {
    "azure-functions-openapi",
    "azure-functions-validation",
    "pydantic",
    "azure-functions-doctor",
}


def _generate(
    tmp_path: Path,
    name: str,
    preset: str,
    features: frozenset[str] = frozenset(),
) -> Path:
    return scaffold_project(
        name,
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name=preset,
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
            include_openapi="openapi" in features,
            include_validation="validation" in features,
            include_doctor="doctor" in features,
        ),
    )


def _files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _requirement_names(requirements: list[str]) -> set[str]:
    return {re.split(r"[<>=!~;\[ ]", requirement, maxsplit=1)[0] for requirement in requirements}


def _project(root: Path) -> tuple[set[str], set[str]]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dev = project.get("optional-dependencies", {}).get("dev", [])
    return _requirement_names(project["dependencies"]), _requirement_names(dev)


@pytest.fixture
def api_project(tmp_path: Path) -> Path:
    spec = INTENT_SPECS["api/new"]
    return _generate(tmp_path, "api", spec.preset, spec.features)


def test_afs_new_is_the_production_oriented_api_scaffold(api_project: Path) -> None:
    files = _files(api_project)
    runtime, dev = _project(api_project)

    assert len(files) == 25
    assert GENERATED_TESTS <= files
    assert not any(name.startswith(".github/") for name in files), "CI workflow is opt-in"
    assert runtime == BASE_RUNTIME | API_EXTRAS
    assert dev == {"pytest", "ruff", "mypy"}


def test_standard_preset_drops_the_api_features_but_keeps_the_layout(
    tmp_path: Path, api_project: Path
) -> None:
    standard = _generate(tmp_path, "standard", "standard")
    runtime, dev = _project(standard)

    assert _files(standard) == _files(api_project)
    assert runtime == BASE_RUNTIME
    assert dev == {"pytest", "ruff"}


def test_minimal_preset_changes_tooling_only(tmp_path: Path, api_project: Path) -> None:
    minimal = _generate(tmp_path, "minimal", "minimal")
    runtime, dev = _project(minimal)

    assert _files(minimal) == _files(api_project) - GENERATED_TESTS
    assert len(_files(minimal)) == 23
    assert {"app/core/logging.py", "app/services/health_service.py"} <= _files(minimal)
    assert runtime == BASE_RUNTIME
    assert dev == set()


def test_guide_documents_the_measured_comparison() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    section = text.split("#### Choosing an HTTP starter")[1].split("### Timer Template")[0]

    for command in ("afs new", "afs advanced new <name>", "--preset minimal", "func init"):
        assert command in section
    assert "| 25 |" in section and "| 23 |" in section
