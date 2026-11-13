"""The troubleshooting guide must list every registered template (issue #476)."""

from __future__ import annotations

from pathlib import Path
import re

from azure_functions_scaffold.template_registry import list_templates

TROUBLESHOOTING = Path(__file__).resolve().parent.parent / "docs" / "guide" / "troubleshooting.md"
LISTING_RE = re.compile(r"Supported templates are ([^\n]+)\.")


def _documented_templates() -> list[str]:
    match = LISTING_RE.search(TROUBLESHOOTING.read_text(encoding="utf-8"))
    assert match is not None, "troubleshooting.md must contain a 'Supported templates are ...' line"
    return re.findall(r"`([^`]+)`", match.group(1))


def test_troubleshooting_lists_exactly_the_registered_templates() -> None:
    registered = [template.name for template in list_templates()]
    assert sorted(_documented_templates()) == sorted(registered)


def test_troubleshooting_points_to_authoritative_cli_listing() -> None:
    assert "`afs templates`" in TROUBLESHOOTING.read_text(encoding="utf-8")
