"""The committed historical exceptions, exercised against the audit with fixtures (#492).

The generic behaviour is covered by ``test_release_audit.py``. These cases use this repository's
own history: a published release, the ``v0.7.2`` and ``v0.9.0`` candidates whose Azure
certification failed before publish, a published tag that had no GitHub Release, and the early tags
that never reached PyPI.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from tools import release_audit as ra

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
OLD = NOW - timedelta(days=30)
CFG = ra.Config.load(ROOT / ra.CONFIG_PATH)


def tag(version: str, declared: str | None = None, on_mainline: bool = True) -> ra.TagFact:
    return ra.TagFact(f"v{version}", "a" * 40, OLD, declared or version, on_mainline)


def release(version: str) -> ra.ReleaseFact:
    return ra.ReleaseFact(f"v{version}", False, OLD)


def pypi(version: str) -> ra.PyPIFact:
    return ra.PyPIFact(version, False, OLD)


def facts(
    tags: list[ra.TagFact],
    releases: list[ra.ReleaseFact],
    published: list[ra.PyPIFact],
    changelog: set[str],
) -> ra.Facts:
    return ra.Facts(
        tags={t.name.removeprefix("v"): t for t in tags},
        releases={r.tag.removeprefix("v"): r for r in releases},
        pypi={p.version: p for p in published},
        changelog_versions=frozenset(changelog),
    )


def only(*versions: str) -> ra.Config:
    """The committed exceptions for just these versions, so a one-version fixture is not stale."""
    return ra.Config(
        repo=CFG.repo,
        package=CFG.package,
        mainline=CFG.mainline,
        approved={v: CFG.approved[v] for v in versions},
    )


def test_the_committed_exceptions_are_exactly_the_documented_cases() -> None:
    assert set(CFG.approved) == {"0.1.0", "0.3.0", "0.3.1", "0.5.1", "0.7.2", "0.9.0"}
    assert CFG.approved["0.9.0"].codes == {ra.RELEASE_WITHOUT_PYPI}
    assert CFG.approved["0.7.2"].codes == {ra.RELEASE_WITHOUT_PYPI}
    assert CFG.approved["0.5.1"].codes == {ra.TAG_VERSION_MISMATCH, ra.RELEASE_WITHOUT_PYPI}
    assert CFG.approved["0.3.0"].codes == {
        ra.TAG_VERSION_MISMATCH,
        ra.TAG_ONLY,
        ra.CHANGELOG_MISSING,
    }
    assert CFG.approved["0.3.1"].codes == {ra.TAG_ONLY}
    assert CFG.approved["0.1.0"].codes == {ra.TAG_ONLY}


def test_a_published_release_is_clean() -> None:
    clean = facts([tag("0.9.1")], [release("0.9.1")], [pypi("0.9.1")], {"0.9.1"})
    report = ra.audit(only(), clean, NOW)
    assert report.ok
    assert report.findings == ()


def test_the_failed_candidates_are_documented_exceptions_not_new_defects() -> None:
    candidates = facts(
        [tag("0.7.2"), tag("0.9.0")],
        [release("0.7.2"), release("0.9.0")],
        [],
        {"0.7.2", "0.9.0"},
    )
    assert not ra.audit(only(), candidates, NOW).ok
    report = ra.audit(only("0.7.2", "0.9.0"), candidates, NOW)
    assert report.ok
    assert [f.approved for f in report.findings] == [(ra.RELEASE_WITHOUT_PYPI,)] * 2


def test_a_new_unpublished_release_is_still_reported_next_to_the_exceptions() -> None:
    both = facts(
        [tag("0.9.0"), tag("0.10.0")],
        [release("0.9.0"), release("0.10.0")],
        [],
        {"0.9.0", "0.10.0"},
    )
    report = ra.audit(only("0.9.0"), both, NOW)
    assert not report.ok
    assert [f.version for f in report.findings if f.failing] == ["0.10.0"]


def test_an_exception_does_not_cover_the_neighbouring_candidate() -> None:
    candidates = facts(
        [tag("0.7.2"), tag("0.9.0")],
        [release("0.7.2"), release("0.9.0")],
        [],
        {"0.7.2", "0.9.0"},
    )
    report = ra.audit(only("0.7.2"), candidates, NOW)
    assert not report.ok
    assert [f.version for f in report.findings if f.failing] == ["0.9.0"]


def test_the_tag_without_a_version_bump_v0_5_1_is_recognised_in_full() -> None:
    unbumped = facts([tag("0.5.1", declared="0.5.0")], [release("0.5.1")], [], {"0.5.1"})
    codes = {ra.TAG_VERSION_MISMATCH, ra.RELEASE_WITHOUT_PYPI}
    assert ra.audit(only(), unbumped, NOW).findings[0].unapproved == tuple(sorted(codes))
    assert ra.audit(only("0.5.1"), unbumped, NOW).ok


def test_the_early_tag_only_versions_are_allowed_only_because_they_are_documented() -> None:
    tag_only = facts([tag("0.1.0")], [], [], {"0.1.0"})
    assert not ra.audit(only(), tag_only, NOW).ok
    assert ra.audit(only("0.1.0"), tag_only, NOW).ok

    duplicate = facts([tag("0.3.0", declared="0.3.1")], [], [], set())
    codes = {ra.TAG_VERSION_MISMATCH, ra.TAG_ONLY, ra.CHANGELOG_MISSING}
    assert ra.audit(only(), duplicate, NOW).findings[0].unapproved == tuple(sorted(codes))
    assert ra.audit(only("0.3.0"), duplicate, NOW).ok

    assert ra.audit(only("0.3.1"), facts([tag("0.3.1")], [], [], {"0.3.1"}), NOW).ok


def test_a_published_tag_without_a_github_release_is_reported() -> None:
    missing = facts([tag("0.4.0")], [], [pypi("0.4.0")], {"0.4.0"})
    report = ra.audit(only(), missing, NOW)
    assert not report.ok
    assert report.findings[0].unapproved == (ra.PYPI_WITHOUT_RELEASE,)
    restored = facts([tag("0.4.0")], [release("0.4.0")], [pypi("0.4.0")], {"0.4.0"})
    assert ra.audit(only(), restored, NOW).ok
