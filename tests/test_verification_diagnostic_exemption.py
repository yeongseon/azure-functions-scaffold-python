from datetime import date
import json
from pathlib import Path
import sys

import pytest

from tools.verification_diagnostics import classify, classify_template
from tools.verification_manifest import REQUIRED_DIAGNOSTICS, TEMPLATES

TODAY = date(2026, 10, 23)
SHORT_CIRCUIT = json.dumps(
    {
        "metadata": {"tool_version": "0.23.1", "programming_model": "unknown"},
        "results": [
            {
                "items": [
                    {"rule_id": "check_programming_model_v2", "status": "fail", "severity": "error"}
                ]
            }
        ],
    }
)


def test_langgraph_known_short_circuit_is_visible_incomplete_not_pass() -> None:
    result = classify_template(SHORT_CIRCUIT, 1, template="langgraph", today=TODAY)
    assert result.category == "INCOMPLETE"
    assert result.exit_code == 0
    assert result.exemption is not None
    assert result.exemption.owner == "yeongseon"
    assert result.exemption.issue.endswith("/azure-functions-doctor-python/issues/590")
    assert classify(SHORT_CIRCUIT, 1).exit_code != 0


@pytest.mark.parametrize("template", [name for name in TEMPLATES if name != "langgraph"])
def test_other_templates_never_exempt_missing_diagnostics(template: str) -> None:
    assert classify_template(SHORT_CIRCUIT, 1, template=template, today=TODAY).exit_code != 0


def test_langgraph_exemption_expires() -> None:
    result = classify_template(SHORT_CIRCUIT, 1, template="langgraph", today=TODAY)
    assert result.exemption is not None
    assert (
        classify_template(
            SHORT_CIRCUIT, 1, template="langgraph", today=result.exemption.expires
        ).exit_code
        != 0
    )


@pytest.mark.parametrize("template", TEMPLATES)
@pytest.mark.parametrize("omitted", REQUIRED_DIAGNOSTICS)
def test_omitted_required_diagnostic_still_blocks_every_template(
    template: str, omitted: str
) -> None:
    document = json.dumps(
        {
            "results": [
                {
                    "items": [
                        {"rule_id": rule, "status": "pass", "severity": "info"}
                        for rule in REQUIRED_DIAGNOSTICS
                        if rule != omitted
                    ]
                }
            ]
        }
    )
    assert classify_template(document, 0, template=template, today=TODAY).exit_code != 0


@pytest.mark.parametrize(
    "document,code",
    [
        ("invalid", 1),
        (SHORT_CIRCUIT, 2),
        (SHORT_CIRCUIT, 139),
        (SHORT_CIRCUIT.replace("0.23.1", "0.24.0"), 1),
        (SHORT_CIRCUIT.replace("check_programming_model_v2", "check_host_json"), 1),
    ],
)
def test_unrecognized_langgraph_failures_are_not_exempt(document: str, code: int) -> None:
    assert classify_template(document, code, template="langgraph", today=TODAY).exit_code != 0


def test_diagnose_persists_nonpassing_exemption_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools import verification_diagnostics as diagnostics

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "doctor.json").write_text(SHORT_CIRCUIT)
    monkeypatch.setattr(diagnostics, "run", lambda *args, **kwargs: 1)
    result = diagnostics.diagnose(tmp_path, Path(sys.executable), logs, template="langgraph")
    assert result.category == "INCOMPLETE"
    summary = json.loads((tmp_path / "diagnostics/summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["required"] is False
    assert summary["exit_code"] == 1
    assert summary["passed"] == 0
