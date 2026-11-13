"""Regression test: the troubleshooting guide must list the registered templates and presets.

The guide names the valid values for ``Unknown template`` and ``Unknown preset`` errors. The lists
are read from ``list_templates()`` and ``list_presets()`` so a new template or preset cannot be
added without the guide being updated.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

from azure_functions_scaffold.template_registry import list_presets, list_templates

TROUBLESHOOTING = Path(__file__).resolve().parent.parent / "docs" / "guide" / "troubleshooting.md"


def _documented(kind: str) -> list[str]:
    text = TROUBLESHOOTING.read_text(encoding="utf-8")
    match = re.search(rf"^Supported {kind} are (.+)\.$", text, flags=re.MULTILINE)
    assert match is not None, (
        f"docs/guide/troubleshooting.md has no 'Supported {kind} are ...' line"
    )
    return re.findall(r"`([^`]+)`", match.group(1))


@pytest.mark.parametrize(
    ("kind", "registered"),
    [
        ("templates", [spec.name for spec in list_templates()]),
        ("presets", [spec.name for spec in list_presets()]),
    ],
)
def test_troubleshooting_lists_every_registered_name(kind: str, registered: list[str]) -> None:
    documented = _documented(kind)

    assert sorted(documented) == sorted(registered), (
        f"docs/guide/troubleshooting.md lists {documented} for {kind}, "
        f"but the registry has {registered}"
    )


def test_troubleshooting_points_to_authoritative_cli_listing() -> None:
    assert "`afs templates`" in TROUBLESHOOTING.read_text(encoding="utf-8")
