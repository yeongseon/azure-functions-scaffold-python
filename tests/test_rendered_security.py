from pathlib import Path

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options, list_templates
from tools.rendered_security import check_structures, render_inventory, scan_python
from tools.security_report import Status


@pytest.mark.parametrize("template", [t.name for t in list_templates()])
def test_generated_workflows_are_pinned_and_read_only(tmp_path: Path, template: str) -> None:
    scaffold_project(
        "project",
        tmp_path,
        template_name=template,
        options=build_project_options(
            preset_name="standard",
            python_version="3.11",
            include_github_actions=True,
            initialize_git=False,
        ),
    )
    result = check_structures(tmp_path)
    assert result.status == Status.PASS, result.findings


def test_empty_generated_python_is_incomplete(tmp_path: Path) -> None:
    assert scan_python(tmp_path).status == Status.INCOMPLETE


def test_unreviewed_generated_suppression_is_incomplete(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import subprocess  # nosec B404\n")
    assert scan_python(tmp_path).status == Status.INCOMPLETE


def test_unknown_action_commit_cannot_pass(tmp_path: Path) -> None:
    workflow = tmp_path / "project/.github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "permissions:\n  contents: read\njobs:\n  test:\n    steps:\n"
        "      - uses: actions/checkout@" + "0" * 40 + " # v7.0.1\n"
    )
    assert check_structures(tmp_path).status == Status.FAIL


def test_scanner_receives_enabled_and_disabled_feature_branches(tmp_path: Path) -> None:
    projects = render_inventory(tmp_path)
    schemas = [p.read_text() for p in tmp_path.glob("http-*/app/schemas/webhooks.py")]
    handlers = [p.read_text() for p in tmp_path.glob("http-*/app/functions/webhooks.py")]
    assert any("dataclass" in source for source in schemas)
    assert any("BaseModel" in source for source in schemas)
    assert any("WebhookEvent.model_validate" not in source for source in handlers)
    assert any("WebhookEvent.model_validate" in source for source in handlers)
    check = scan_python(tmp_path)
    assert check.status == Status.PASS, check
    assert len(projects) == 60
    assert check.counts["files"] == len(
        [p for p in tmp_path.rglob("*.py") if "tests" not in p.relative_to(tmp_path).parts]
    )
