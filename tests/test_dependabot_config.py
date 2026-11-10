"""The minimum-dependency fixture must stay out of Dependabot's pip updates (#495).

``ci/constraints-min.txt`` pins every declared dependency to its lowest supported version on
purpose. Dependabot's pip updater reads every requirements-style ``*.txt`` in the configured
directory and in each directory directly below it, so it raised these pins again (#487, #488)
even after the file had moved under ``ci/`` (#446). ``exclude-paths`` in ``.github/dependabot.yml``
is the mechanism that keeps the file out; these tests fail if that entry is removed, misspelled or
changed to something that no longer matches, or if it grows wide enough to hide ``pyproject.toml``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _REPO_ROOT / ".github" / "dependabot.yml"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci-test.yml"
_FIXTURE = "ci/constraints-min.txt"
_MANIFEST = "pyproject.toml"


def _excluded(path: str, patterns: list[str]) -> bool:
    """Whether dependabot-core's ``FileFiltering`` excludes ``path``.

    Mirrors only its exact-path, directory and ``dir/**`` rules, which is all this repository
    needs. A glob that relies on ``fnmatch`` is not recognised, so changing the entry to one
    fails the test and gets looked at instead of being trusted.
    """
    for pattern in patterns:
        base = pattern.removesuffix("/")
        if path in (pattern, base) or path.startswith((f"{pattern}/", f"{base}/")):
            return True
        root = pattern.removesuffix("/**")
        if root != pattern and root and (path == root or path.startswith(f"{root}/")):
            return True
    return False


def _pip_updates() -> list[dict[str, Any]]:
    config = yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))
    return [update for update in config["updates"] if update["package-ecosystem"] == "pip"]


@pytest.mark.parametrize("pattern", ["ci/constraints-min.txt", "ci/**", "ci/", "ci"])
def test_the_matcher_accepts_every_spelling_that_reaches_the_fixture(pattern: str) -> None:
    assert _excluded(_FIXTURE, [pattern])


@pytest.mark.parametrize(
    "patterns",
    [
        [],
        ["ci/constraint-min.txt"],
        ["docs/**"],
        ["cii/**"],
        ["tests/constraints-min.txt"],
        ["ci/other/**"],
        ["/**"],
    ],
)
def test_the_matcher_rejects_entries_that_miss_the_fixture(patterns: list[str]) -> None:
    assert not _excluded(_FIXTURE, patterns)


def test_ci_installs_the_floors_from_the_file_that_is_excluded() -> None:
    assert (_REPO_ROOT / _FIXTURE).is_file()
    assert f"-c {_FIXTURE}" in _CI_WORKFLOW.read_text(encoding="utf-8")


def test_every_pip_update_excludes_the_minimum_dependency_fixture() -> None:
    updates = _pip_updates()
    assert updates, ".github/dependabot.yml has no pip update"
    for update in updates:
        patterns = update.get("exclude-paths", [])
        assert _excluded(_FIXTURE, patterns), (
            f"the pip update for {update.get('directory', update.get('directories'))!r} does "
            f"not exclude {_FIXTURE}, so Dependabot would raise its deliberately minimal pins "
            f"again (#487, #488). exclude-paths is {patterns!r}; use the exact path or ci/**."
        )


def test_the_exclusion_does_not_hide_the_real_manifest() -> None:
    for update in _pip_updates():
        patterns = update.get("exclude-paths", [])
        assert not _excluded(_MANIFEST, patterns), (
            f"exclude-paths {patterns!r} also hides {_MANIFEST}, which would stop Dependabot "
            "from maintaining the runtime and development dependencies."
        )
