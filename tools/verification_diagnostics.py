from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
import json
from pathlib import Path
from typing import Literal

from tools.verification_evidence import Summary, publish, redact, save
from tools.verification_manifest import (
    DIAGNOSTIC_EXEMPTIONS,
    REQUIRED_DIAGNOSTICS,
    DiagnosticExemption,
)
from tools.verification_process import run

Category = Literal["PASS", "ADVISORY", "REQUIRED_FINDING", "CLI_ERROR", "CRASH", "INCOMPLETE"]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    category: Category
    exit_code: int
    exemption: DiagnosticExemption | None = None


def classify_template(document: str, code: int, *, template: str, today: date) -> Diagnostic:
    result = classify(document, code)
    exemption = DIAGNOSTIC_EXEMPTIONS.get(template)
    if exemption is None or today >= exemption.expires or code != 1:
        return result
    try:
        payload = json.loads(document)
        metadata = payload["metadata"]
        findings = [item for group in payload["results"] for item in group["items"]]
        if (
            metadata["tool_version"] == exemption.doctor_version
            and metadata["programming_model"] == "unknown"
            and len(findings) == 1
            and findings[0]["rule_id"] == "check_programming_model_v2"
            and findings[0]["status"] == "fail"
            and findings[0]["severity"] == "error"
        ):
            return Diagnostic("INCOMPLETE", 0, exemption)
    except (ValueError, KeyError, TypeError):
        return result
    return result


def classify(document: str, code: int) -> Diagnostic:
    if code == 2:
        return Diagnostic("CLI_ERROR", code)
    if code not in (0, 1):
        return Diagnostic("CRASH", code)
    try:
        payload = json.loads(document)
        results = payload["results"]
        if not isinstance(results, list) or not results:
            raise ValueError("Missing diagnostics results")
        findings = [item for result in results for item in result["items"]]
        if not findings:
            raise ValueError("Missing diagnostic findings")
        for item in findings:
            if item["status"] not in {"pass", "warn", "fail", "skip"}:
                raise ValueError("Invalid finding status")
            if item["severity"] not in {"error", "warning", "info"}:
                raise ValueError("Invalid finding severity")
            if not isinstance(item["rule_id"], str):
                raise ValueError("Missing rule identity")
        if not set(REQUIRED_DIAGNOSTICS).issubset({item["rule_id"] for item in findings}):
            raise ValueError("Missing required diagnostic identities")
        blocking = any(
            item["rule_id"] in REQUIRED_DIAGNOSTICS and item["status"] in {"fail", "skip"}
            for item in findings
        )
        advisory = any(item["status"] in {"fail", "warn"} for item in findings)
    except (ValueError, KeyError, TypeError):
        return Diagnostic("CRASH", code or 1)
    if blocking:
        return Diagnostic("REQUIRED_FINDING", 1)
    return Diagnostic("ADVISORY" if advisory or code else "PASS", 0)


def diagnose(project: Path, python: Path, directory: Path, *, template: str = "") -> Diagnostic:
    directory.mkdir(parents=True, exist_ok=True)
    code = run(
        [
            str(python.parent / "azure-functions-doctor"),
            "doctor",
            "--path",
            str(project),
            "--format",
            "json",
            "--output",
            str(directory / "doctor.json"),
        ],
        directory / "doctor.stderr.log",
        timeout=120,
        cwd=project,
    )
    output = directory / "doctor.json"
    document = redact(output.read_text()) if output.exists() else ""
    if output.exists():
        output.write_text(document)
    diagnostic = classify_template(
        document, code, template=template, today=datetime.now(UTC).date()
    )
    if exemption := diagnostic.exemption:
        publish(
            save(
                directory.parent / "diagnostics",
                Summary(
                    1,
                    f"{template}-diagnostics",
                    ("azure-functions-doctor", "doctor"),
                    1,
                    0,
                    0,
                    0,
                    "INCOMPLETE",
                    code,
                    required=False,
                    reason=f"{exemption.reason}; owner={exemption.owner}; "
                    f"expires={exemption.expires}; "
                    f"issue={exemption.issue}; doctor={exemption.doctor_version}",
                ),
            )
        )
    return diagnostic
