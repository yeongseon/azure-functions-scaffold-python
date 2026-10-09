from __future__ import annotations

from pathlib import Path
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_changed_paths.sh"



def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def commit_file(repository: Path, name: str, content: str) -> str:
    (repository / name).write_text(content, encoding="utf-8")
    git(repository, "add", name)
    git(
        repository,
        "-c",
        "user.name=CI Test",
        "-c",
        "user.email=ci@example.invalid",
        "commit",
        "-m",
        name,
    )
    return git(repository, "rev-parse", "HEAD")


def test_push_range_rejects_non_ancestor_before_sha(tmp_path: Path) -> None:
    # Given: a force-push range whose before commit is not an ancestor of the new SHA.
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "--initial-branch=main")
    before = commit_file(repository, "before.txt", "before\n")
    git(repository, "checkout", "--orphan", "replacement")
    git(repository, "rm", "-rf", ".")
    after = commit_file(repository, "after.txt", "after\n")

    # When: the push range wrapper computes changed paths.
    completed = subprocess.run(
        ["bash", str(SCRIPT), "push", "", "", before, after],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: it rejects the unsafe range so the workflow selects fail-safe full CI.
    assert completed.returncode != 0


def test_push_range_lists_paths_for_ancestor_before_sha(tmp_path: Path) -> None:
    # Given: a normal push range whose before commit is an ancestor of the new SHA.
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "--initial-branch=main")
    before = commit_file(repository, "before.txt", "before\n")
    after = commit_file(repository, "after.txt", "after\n")

    # When: the push range wrapper computes changed paths.
    completed = subprocess.run(
        ["bash", str(SCRIPT), "push", "", "", before, after],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: it emits the changed path for classification.
    assert completed.returncode == 0
    assert completed.stdout.splitlines() == ["after.txt"]
