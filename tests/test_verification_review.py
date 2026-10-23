import json
from pathlib import Path
import sys

import pytest

from tools.verification_diagnostics import classify
from tools.verification_evidence import Summary, redact, save
from tools.verification_generated import checked
from tools.verification_manifest import REQUIRED_DIAGNOSTICS


@pytest.mark.parametrize("omitted", REQUIRED_DIAGNOSTICS)
def test_omitted_required_diagnostic_blocks(omitted: str) -> None:
    document = json.dumps(
        {
            "results": [
                {
                    "items": [
                        {"rule_id": name, "severity": "info", "status": "pass"}
                        for name in REQUIRED_DIAGNOSTICS
                        if name != omitted
                    ]
                }
            ]
        }
    )
    assert classify(document, 0).exit_code != 0


def test_checked_ignores_conflicting_source_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "fake/azure_functions_scaffold"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text("raise RuntimeError('checkout imported')\n")
    monkeypatch.setenv("PYTHONPATH", str(fake.parent))
    checked(
        [sys.executable, "-c", "import azure_functions_scaffold"],
        tmp_path / "cli.log",
        cwd=tmp_path,
    )


@pytest.mark.parametrize(
    "text",
    [
        '{"Authorization": "Bearer CANARY_a"}',
        "{'Proxy-Authorization': 'Basic CANARY_b'}",
        '{"password": "alpha CANARY_c beta"}',
        '{"token": "with \\"escaped\\" CANARY_d"}',
        "SharedAccessKey=CANARY_e;InstrumentationKey=CANARY_f",
        '<failure message="Authorization: Bearer CANARY_g">x</failure>',
    ],
)
def test_redact_whole_credential_values(text: str) -> None:
    assert "CANARY" not in redact(text)


def test_save_preserves_png_symlink_and_json_structure(tmp_path: Path) -> None:
    png = b"\x89PNG\r\n\x1a\n\xff\xfe\x00binary"
    (tmp_path / "chart.png").write_bytes(png)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.log"
    outside.write_text("password=CANARY")
    (tmp_path / "link.log").symlink_to(outside)
    (tmp_path / "nested.json").write_text(
        '{"password":123,"nested":["Authorization: Bearer CANARY"]}'
    )
    save(tmp_path, Summary(1, "test", ('Authorization: "Bearer CANARY"',), 1, 1, 0, 0, "PASS", 0))
    assert (tmp_path / "chart.png").read_bytes() == png
    assert outside.read_text() == "password=CANARY"
    assert "CANARY" not in (tmp_path / "summary.json").read_text()
    assert json.loads((tmp_path / "nested.json").read_text())["password"] == 123


def test_known_secret_replaced_whole_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_API_TOKEN", 'pre;fix&CANARY "value"')
    assert "CANARY" not in redact('seen pre;fix&CANARY "value"')
    assert "CANARY" not in redact(json.dumps({"x": 'pre;fix&CANARY "value"'}))
