from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README_FILES = ("README.md", "README.ko.md", "README.ja.md", "README.zh-CN.md")


@pytest.mark.parametrize("readme_name", README_FILES)
def test_readme_comparison_names_generated_layout(readme_name: str) -> None:
    content = (REPO_ROOT / readme_name).read_text(encoding="utf-8")

    assert "INTENTIONALLY-MISSING-CI-SCENARIO" in content
    assert "`api/`, `domain/`, `infra/`" not in content


@pytest.mark.parametrize("readme_name", README_FILES)
def test_readme_documents_azd_infrastructure_boundary(readme_name: str) -> None:
    content = (REPO_ROOT / readme_name).read_text(encoding="utf-8")

    assert "`--azd`" in content
    assert "`azure.yaml`" in content
    assert "`infra/`" in content
