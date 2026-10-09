from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-test.yml"
FULL_MATRIX = {
    "docs_only": "false",
    "docs_changed": "true",
    "full_required": "true",
}


def changes_script() -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    script = workflow["jobs"]["changes"]["steps"][1]["run"]
    assert isinstance(script, str)
    return script


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def run_changes(repository: Path, event: dict[str, str]) -> dict[str, str]:
    output = repository / "github-output"
    completed = subprocess.run(
        ["bash", "-c", changes_script()],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
        env=os.environ
        | event
        | {
            "GITHUB_OUTPUT": str(output),
            "RUNNER_TEMP": str(repository),
        },
    )
    assert completed.returncode == 0, completed.stderr
    return dict(line.split("=", 1) for line in output.read_text().splitlines())


def initialized_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "tools").mkdir(parents=True)
    for script in ("ci_changed_paths.sh", "ci_classify_changes.sh"):
        shutil.copy2(REPO_ROOT / "tools" / script, repository / "tools" / script)
    (repository / "README.md").write_text("base\n", encoding="utf-8")
    git(repository, "init", "--initial-branch=main")
    git(repository, "config", "user.name", "CI Test")
    git(repository, "config", "user.email", "ci@example.invalid")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "base")
    return repository


def pull_event(base: str, head: str) -> dict[str, str]:
    return {
        "EVENT_NAME": "pull_request",
        "BASE_SHA": base,
        "HEAD_SHA": head,
        "HEAD_REPOSITORY": "owner/repo",
        "REPOSITORY": "owner/repo",
        "PR_NUMBER": "1",
        "BEFORE_SHA": "",
        "SHA": "",
    }


def push_event(before: str, head: str) -> dict[str, str]:
    return {
        "EVENT_NAME": "push",
        "BASE_SHA": "",
        "HEAD_SHA": "",
        "HEAD_REPOSITORY": "",
        "REPOSITORY": "owner/repo",
        "PR_NUMBER": "",
        "BEFORE_SHA": before,
        "SHA": head,
    }


@pytest.mark.parametrize("event_name", ["pull_request", "push"])
def test_git_diff_failure_selects_full_matrix(event_name: str, tmp_path: Path) -> None:
    # Given: a valid event range and a git executable that fails only on diff.
    repository = initialized_repository(tmp_path)
    base = git(repository, "rev-parse", "HEAD")
    (repository / "README.md").write_text("head\n", encoding="utf-8")
    git(repository, "commit", "-am", "head")
    head = git(repository, "rev-parse", "HEAD")
    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    real_git = shutil.which("git")
    assert real_git is not None
    (binary_directory / "git").write_text(
        f'#!/usr/bin/env bash\nif [ "$1" = diff ]; then exit 42; fi\nexec "{real_git}" "$@"\n',
        encoding="utf-8",
    )
    (binary_directory / "git").chmod(0o755)
    event = pull_event(base, head) if event_name == "pull_request" else push_event(base, head)
    event["PATH"] = f"{binary_directory}{os.pathsep}{os.environ['PATH']}"

    # When: the complete changes-job shell runs.
    result = run_changes(repository, event)

    # Then: the prewritten fail-safe outputs require the full matrix.
    assert result == FULL_MATRIX


def test_fork_modified_classifier_cannot_influence_result(tmp_path: Path) -> None:
    # Given: trusted base scripts and a fork head that replaces the classifier.
    repository = initialized_repository(tmp_path)
    base = git(repository, "rev-parse", "HEAD")
    origin = tmp_path / "origin.git"
    git(tmp_path, "clone", "--bare", str(repository), str(origin))
    git(repository, "remote", "add", "origin", str(origin))
    git(repository, "checkout", "-b", "fork")
    (repository / "tools" / "ci_classify_changes.sh").write_text(
        "#!/usr/bin/env bash\n"
        "printf 'docs_only=true\\ndocs_changed=false\\nfull_required=false\\n'\n",
        encoding="utf-8",
    )
    git(repository, "add", ".")
    git(repository, "commit", "-m", "replace classifier")
    fork_head = git(repository, "rev-parse", "HEAD")
    git(repository, "checkout", "main")
    git(repository, "merge", "--no-ff", "fork", "-m", "merge fork")
    merge = git(repository, "rev-parse", "HEAD")
    git(repository, "push", "origin", f"{merge}:refs/pull/1/merge")
    git(repository, "reset", "--hard", base)
    event = pull_event(base, fork_head)
    event["HEAD_REPOSITORY"] = "attacker/fork"

    # When: the fork path is classified from the trusted base checkout.
    result = run_changes(repository, event)

    # Then: the malicious classifier cannot suppress the full matrix.
    assert result == FULL_MATRIX
