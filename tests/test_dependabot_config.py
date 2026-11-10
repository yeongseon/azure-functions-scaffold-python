"""The minimum-dependency fixture must stay out of Dependabot's pip updates (#495).

``ci/constraints-min.txt`` pins every declared dependency to its lowest supported version on
purpose. Dependabot's pip updater reads every requirements-style ``*.txt`` in the configured
directory and in each directory directly below it, so it raised these pins again (#487, #488)
even after the file had moved under ``ci/`` (#446). ``exclude-paths`` in ``.github/dependabot.yml``
is the mechanism that keeps the file out; these tests fail if that entry is removed, misspelled or
changed to something that no longer matches, or if it grows wide enough to hide ``pyproject.toml``.

The file must also stay valid for GitHub. A cooldown key that GitHub rejects for an ecosystem
invalidates the whole file, and the exclusion above then never takes effect (#495).
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


# GitHub documents which package ecosystems accept the ``semver-*-days`` cooldown keys:
# https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference
# For the ecosystems below only ``default-days`` is valid. One rejected key invalidates the whole
# file: GitHub keeps running the last valid configuration and reports the error only in the
# ``.github/dependabot.yml`` check-run on the default branch, which is not a required check. The
# published JSON schema accepts these keys everywhere, so schema validation cannot catch it and
# this test is the local guard.
_NO_SEMVER_COOLDOWN = frozenset(
    {
        "bazel",
        "devcontainers",
        "docker",
        "docker-compose",
        "github-actions",
        "gitsubmodule",
        "helm",
        "nix",
        "opentofu",
        "pre-commit",
        "terraform",
        "vcpkg",
    }
)
_SEMVER_COOLDOWN_KEYS = ("semver-major-days", "semver-minor-days", "semver-patch-days")


def _rejected_cooldown_keys(config: dict[str, Any]) -> list[tuple[str, str]]:
    """The ``(ecosystem, key)`` pairs that GitHub would reject as an invalid configuration."""
    rejected: list[tuple[str, str]] = []
    for update in config["updates"]:
        ecosystem = update["package-ecosystem"]
        if ecosystem in _NO_SEMVER_COOLDOWN:
            cooldown = update.get("cooldown") or {}
            rejected.extend((ecosystem, key) for key in _SEMVER_COOLDOWN_KEYS if key in cooldown)
    return rejected


def test_the_guard_flags_semver_cooldown_keys_only_where_github_rejects_them() -> None:
    tiers = {"default-days": 7, "semver-major-days": 30, "semver-minor-days": 7}
    flagged = {
        "updates": [
            {"package-ecosystem": "github-actions", "cooldown": tiers},
            {"package-ecosystem": "pip", "cooldown": tiers},
        ]
    }
    assert _rejected_cooldown_keys(flagged) == [
        ("github-actions", "semver-major-days"),
        ("github-actions", "semver-minor-days"),
    ]
    clean = {
        "updates": [
            {"package-ecosystem": "github-actions", "cooldown": {"default-days": 7}},
            {"package-ecosystem": "github-actions"},
            {"package-ecosystem": "pip", "cooldown": tiers},
        ]
    }
    assert _rejected_cooldown_keys(clean) == []


def test_dependabot_yml_has_no_cooldown_key_that_github_rejects() -> None:
    config = yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))
    rejected = _rejected_cooldown_keys(config)
    assert not rejected, (
        f"GitHub rejects {rejected!r} and then ignores the whole of .github/dependabot.yml, "
        "including exclude-paths. Keep only default-days for these ecosystems (#495)."
    )
