"""Analyze executable output, never Jinja source or raw scanner diagnostics."""

from __future__ import annotations

import argparse
from dataclasses import replace
from itertools import product
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import (
    build_project_options,
    list_presets,
    list_templates,
)
from tools.security_evidence import classify_bandit
from tools.security_report import Check, Finding, Status, load, mapping, write_report

ACTION_PINS = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1": "v7.0.1",
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97": "v7.0.0",
}


def render_inventory(destination: Path) -> tuple[Path, ...]:
    projects: list[Path] = []
    for template in list_templates():
        for preset, enabled in product(list_presets(), (True, False)):
            options = build_project_options(
                preset_name=preset.name,
                python_version="3.11",
                include_github_actions=True,
                initialize_git=False,
                include_azd=True,
                include_openapi=enabled and "openapi" in template.allowed_features,
                include_validation=enabled and "validation" in template.allowed_features,
                include_doctor=enabled and "doctor" in template.allowed_features,
            )
            root = scaffold_project(
                f"{template.name}-{preset.name}-{'enabled' if enabled else 'disabled'}",
                destination,
                template_name=template.name,
                options=options,
            )
            projects.append(root)
            if template.name == "http":
                add_function(project_root=root, trigger="ai", function_name="ai_added")
    return tuple(projects)


def check_structures(root: Path) -> Check:
    findings: list[Finding] = []
    workflows = sorted(root.glob("**/.github/workflows/*.yml"))
    bicep = sorted(root.rglob("*.bicep"))
    for path in workflows:
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        if not re.search(r"(?m)^permissions:\s*\n  contents: read\s*$", content):
            findings.append(Finding("workflow-permissions", relative, severity="MEDIUM"))
        for line, value in enumerate(content.splitlines(), 1):
            if "uses:" in value:
                pin = re.search(r"uses:\s*(\S+)\s+#\s*(\S+)\s*$", value)
                if pin is None or ACTION_PINS.get(pin[1]) != pin[2]:
                    findings.append(Finding("workflow-pin", relative, line, "MEDIUM"))
    for path in bicep:
        relative = path.relative_to(root).as_posix()
        content = path.read_text(encoding="utf-8")
        for line, value in enumerate(content.splitlines(), 1):
            if re.search(r"(?:password|secret|apiKey)\s*:\s*'[^']+'", value, re.I):
                findings.append(Finding("bicep-literal-secret", relative, line, "HIGH"))
            if re.search(r"(?:httpsOnly|supportsHttpsTrafficOnly)\s*:\s*false", value):
                findings.append(Finding("bicep-https", relative, line, "HIGH"))
            if re.search(
                r"(?:minTlsVersion|minimumTlsVersion)\s*:\s*'(?:1\.0|1\.1|TLS1_[01])'", value
            ):
                findings.append(Finding("bicep-tls", relative, line, "HIGH"))
    return Check(
        "rendered-structures",
        ("generated-workflows", "generated-bicep"),
        Status.FAIL if findings else (Status.PASS if workflows else Status.INCOMPLETE),
        0,
        counts={"workflows": len(workflows), "bicep": len(bicep)},
        findings=tuple(findings),
        message="Bicep absent: provisioning, required TLS flags and Azure deployment unverified."
        if not bicep
        else "Only present literals/flags checked; no Azure validation.",
    )


def scan_python(root: Path) -> Check:
    files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if "tests" not in path.relative_to(root).parts
    }
    if not files:
        return Check("rendered-bandit", ("generated-python",), Status.INCOMPLETE, None)
    if any("nosec" in (root / name).read_text(encoding="utf-8") for name in files):
        return Check(
            "rendered-bandit",
            ("generated-python",),
            Status.INCOMPLETE,
            None,
            message="Unexpected generated suppression.",
        )
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                "-q",
                "-r",
                ".",
                "-x",
                "tests",
                "-f",
                "json",
                "--ignore-nosec",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        check = classify_bandit(process.stdout, process.returncode, floor=len(files))
        scanned = {
            name.removeprefix("./")
            for name in mapping(load(process.stdout)["metrics"])
            if name != "_totals"
        }
        if scanned != files and check.status != Status.TOOL_ERROR:
            check = replace(
                check, status=Status.INCOMPLETE, message="Generated inventory mismatch."
            )
        return replace(check, name="rendered-bandit", scope=("generated-python",))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        return Check(
            "rendered-bandit",
            ("generated-python",),
            Status.TOOL_ERROR,
            None,
            message="Generated scan failed; diagnostics discarded.",
        )


def run() -> list[Check]:
    try:
        with tempfile.TemporaryDirectory(prefix="rendered-security-") as temporary:
            root = Path(temporary)
            projects = render_inventory(root)
            check = scan_python(root)
            return [
                replace(check, counts={**check.counts, "projects": len(projects)}),
                check_structures(root),
            ]
    except (OSError, ValueError, RuntimeError):
        return [
            Check(
                "rendered-security",
                ("all-templates-presets",),
                Status.TOOL_ERROR,
                None,
                message="Generation failed; no clean result is available.",
            )
        ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("security-results/rendered"))
    args = parser.parse_args()
    return write_report(run(), args.output)


if __name__ == "__main__":
    raise SystemExit(main())
