"""Guard against README trigger-list drift from generator.ADDABLE_TRIGGERS.

Regression tests for issue #138: the top-level README (and its translations)
must document every trigger exposed by ``generator.ADDABLE_TRIGGERS`` so users
discover the full CLI surface. The ``docs/guide/templates.md`` matrix carries
the per-trigger detail; these tests only assert coverage in the READMEs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from azure_functions_scaffold.generator import ADDABLE_TRIGGERS

REPO_ROOT = Path(__file__).resolve().parent.parent
README_FILES: tuple[str, ...] = (
    "README.md",
    "README.ko.md",
    "README.ja.md",
    "README.zh-CN.md",
)


class TestReadmeTriggerCoverage:
    """Every ADDABLE_TRIGGERS entry must appear in every README variant."""

    @pytest.mark.parametrize("readme_name", README_FILES)
    @pytest.mark.parametrize("trigger", ADDABLE_TRIGGERS)
    def test_trigger_documented_in_readme(self, readme_name: str, trigger: str) -> None:
        readme_path = REPO_ROOT / readme_name
        assert readme_path.exists(), f"Missing README file: {readme_name}"

        content = readme_path.read_text(encoding="utf-8")
        # Trigger name must appear as a backtick-fenced token in the templates
        # table (e.g. `| eventhub |`). We accept either backtick or plain
        # occurrences to stay tolerant of translated section headers, but the
        # trigger name itself must be present verbatim.
        assert trigger in content, (
            f"{readme_name} does not mention ADDABLE_TRIGGERS entry '{trigger}'. "
            f"Update the ## Templates table (and Scope bullet) to keep the CLI "
            f"surface discoverable."
        )

    @pytest.mark.parametrize("readme_name", README_FILES)
    def test_readme_has_templates_section(self, readme_name: str) -> None:
        readme_path = REPO_ROOT / readme_name
        content = readme_path.read_text(encoding="utf-8")
        # English uses '## Templates'; translations use '## 템플릿', '## テンプレート',
        # or '## 模板'. We only require SOME level-2 heading whose body then
        # contains all ADDABLE_TRIGGERS entries — enforced by the sibling test.
        heading_candidates = ("## Templates", "## 템플릿", "## テンプレート", "## 模板")
        assert any(h in content for h in heading_candidates), (
            f"{readme_name} is missing a templates heading. Expected one of {heading_candidates}."
        )
