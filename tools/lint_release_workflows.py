from __future__ import annotations

from pathlib import Path
import re

from tools.lint_workflow_pins import lint as lint_pins


def lint(root: Path | None = None) -> list[str]:
    root = root or Path(__file__).resolve().parents[1]
    errors = lint_pins(root)
    text = (root / ".github/workflows/publish-pypi.yml").read_text()
    match = re.search(r"(?ms)^  publish:\n(?P<body>.*?)(?=^  [\w-]+:|\Z)", text)
    needs = re.search(r"needs:\s*\[([^]]+)\]", match["body"]) if match else None
    if not needs or not {"build", "lib-tests", "azure-e2e"}.issubset(
        item.strip() for item in needs[1].split(",")
    ):
        errors.append("publish must require build, lib-tests and azure-e2e")
    return errors


if __name__ == "__main__":
    errors = lint()
    for error in errors:
        print(error)
    print("Release workflow gates: " + ("FAIL" if errors else "PASS"))
    raise SystemExit(bool(errors))
