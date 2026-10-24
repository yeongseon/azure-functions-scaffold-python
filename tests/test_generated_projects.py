"""Run every registered template's generated project in its own venv and fail closed.

Per project: scaffold (strict preset, this interpreter's minor) -> generated ``make install``
into its own ``.venv`` (this checkout's dev extras cannot mask an undeclared dependency) ->
generated ``make check-all`` (ruff, mypy, pytest) -> pytest rerun with JUnit (at least one test,
none skipped or xfailed) -> Doctor's own required (``minimal``) profile.

The projects are one per registered template, the http template with each ``--with-*`` feature
combination, and the ``afs new`` project after ``afs api add`` / ``afs advanced add``. The
``templates-smoke.yml`` workflow runs these same node ids, one matrix cell each.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import (
    INTENT_SPECS,
    build_project_options,
    list_templates,
)

PYTHON_MINOR = f"{sys.version_info.major}.{sys.version_info.minor}"
DOCTOR_GAP = "langgraph"
# http template feature combinations; an id is the `-`-joined `--with-*` names.
FEATURE_COMBOS = (
    "openapi",
    "validation",
    "doctor",
    "openapi-validation",
    "openapi-validation-doctor",
)
# Applied to the `afs new` project (http, strict, openapi + validation + doctor).
ADD_COMMANDS = (
    ("api", "add", "get-status"),
    ("api", "add-route", "status"),
    ("api", "add-resource", "products"),
    ("advanced", "add", "servicebus", "process-events"),
)


def _run(command: list[str], cwd: Path) -> str:
    """Run a command and return its stdout; a failure shows only output tails, never the env."""
    __tracebackhide__ = True
    done = subprocess.run(
        command,
        cwd=cwd,
        # The generated Makefile has `PYTHON ?= python3`; bind it to this interpreter.
        env={**os.environ, "PYTHON": sys.executable},
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        timeout=900,
    )
    status = done.returncode
    assert status == 0, (
        f"{' '.join(command)} exited {status}:\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}"
    )
    return done.stdout


def _scaffold(tmp_path: Path, template: str, features: frozenset[str] = frozenset()) -> Path:
    return scaffold_project(
        f"{template}-isolated",
        tmp_path,
        template_name=template,
        options=build_project_options(
            preset_name="strict",
            python_version=PYTHON_MINOR,
            include_github_actions=False,
            initialize_git=False,
            include_openapi="openapi" in features,
            include_validation="validation" in features,
            include_doctor="doctor" in features,
        ),
    )


def _assert_doctor_required_profile(root: Path) -> None:
    doctor = [sys.executable, "-m", "azure_functions_doctor.cli", "doctor", "--path", str(root)]
    report = json.loads(_run([*doctor, "--profile", "minimal", "--format", "json"], root))
    evaluated = sum(
        item["status"] != "skip" for group in report["results"] for item in group["items"]
    )
    assert evaluated >= 5, f"Doctor evaluated {evaluated} required rules, expected at least 5"


def _assert_tests_executed(junit: Path) -> None:
    cases = ET.parse(junit).getroot().findall(".//testcase")
    skipped = [case.get("name") for case in cases if case.find("skipped") is not None]
    assert cases and not skipped, f"{len(cases)} tests ran; skipped or xfailed: {skipped}"


def _assert_project_passes(root: Path, *, doctor: bool = True) -> None:
    venv_python = root / ".venv" / "bin" / "python"

    # Own venv: only the project's declared dependencies, on the interpreter running this test.
    _run(["make", "install"], root)
    minor = _run(
        [str(venv_python), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], root
    )
    assert minor.strip() == PYTHON_MINOR

    # The project's own gates. `make check-all` exits 0 when every test is skipped, so rerun
    # pytest with JUnit and require at least one executed test and no skip or xfail.
    _run(["make", "check-all"], root)
    junit = root / "junit.xml"
    _run([str(venv_python), "-m", "pytest", "-q", f"--junitxml={junit}"], root)
    _assert_tests_executed(junit)

    if doctor:
        _assert_doctor_required_profile(root)


@pytest.mark.slow
@pytest.mark.parametrize("template", [template.name for template in list_templates()])
def test_generated_project_passes_in_isolated_venv(tmp_path: Path, template: str) -> None:
    _assert_project_passes(_scaffold(tmp_path, template), doctor=template != DOCTOR_GAP)


@pytest.mark.slow
@pytest.mark.parametrize("combo", FEATURE_COMBOS)
def test_generated_http_features_pass_in_isolated_venv(tmp_path: Path, combo: str) -> None:
    _assert_project_passes(_scaffold(tmp_path, "http", frozenset(combo.split("-"))))


@pytest.mark.slow
def test_generated_http_project_passes_after_add_commands(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, "http", INTENT_SPECS["api/new"].features)
    for command in ADD_COMMANDS:
        result = CliRunner().invoke(app, [*command, "--project-root", str(root)])
        assert result.exit_code == 0, f"afs {' '.join(command)} failed:\n{result.output}"
    _assert_project_passes(root)


@pytest.mark.parametrize(
    "testcases",
    [
        "",
        '<testcase name="t"><skipped/></testcase>',
        '<testcase name="t"><skipped type="pytest.xfail"/></testcase>',
    ],
    ids=["none-collected", "skipped", "xfailed"],
)
def test_suite_without_an_executed_test_fails_the_lane(tmp_path: Path, testcases: str) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(f"<testsuites><testsuite>{testcases}</testsuite></testsuites>")
    with pytest.raises(AssertionError):
        _assert_tests_executed(junit)


def test_suite_with_an_executed_test_passes_the_lane(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite><testcase name="t"/></testsuite></testsuites>')
    _assert_tests_executed(junit)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "azure-functions-doctor-python#590: Doctor cannot classify a LangGraphApp `function_app` "
        "export (programming_model=unknown), so it evaluates none of its required rules. Strict: "
        "once Doctor supports it this XPASS fails the suite; delete this test and DOCTOR_GAP."
    ),
)
def test_langgraph_doctor_required_profile_known_gap(tmp_path: Path) -> None:
    _assert_doctor_required_profile(_scaffold(tmp_path, DOCTOR_GAP))
