"""Characterization of equivalent CLI commands (#455).

Several commands reach one generator through more than one route: ``afs new`` and ``afs api new``,
``afs templates`` and ``afs advanced templates``, ``afs add http`` and ``afs api add`` and
``afs advanced add http``, and so on. These tests pin what each route prints, which exit code it
returns, and which files it writes, so the routing can be consolidated without changing any
supported behavior. Intentional differences between routes are asserted explicitly, not
normalized away.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

runner = CliRunner()


def _tree(root: Path) -> dict[str, str]:
    """Map every file under *root* to a content digest, so differences in content are visible."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def _run(args: list[str], root: Path) -> tuple[int, str, str, dict[str, str]]:
    """Invoke the CLI and return exit code, stdout, stderr and the tree under *root*."""
    result = runner.invoke(app, args)
    return (
        result.exit_code,
        result.stdout.replace(str(root), "<ROOT>"),
        result.stderr.replace(str(root), "<ROOT>"),
        _tree(root),
    )


def _project(parent: Path) -> Path:
    """Scaffold the default API project the add-* commands extend."""
    result = runner.invoke(app, ["new", "proj", "--destination", str(parent), "--no-git"])
    assert result.exit_code == 0, result.output
    return parent / "proj"


def _equivalent(
    tmp_path: Path, first: list[str], second: list[str]
) -> tuple[tuple[int, str, str, dict[str, str]], tuple[int, str, str, dict[str, str]]]:
    """Run *first* and *second* on identical, separate projects; ``{root}`` is the project path."""
    outcomes = []
    for label, template in (("a", first), ("b", second)):
        root = _project(tmp_path / label)
        outcomes.append(_run([part.replace("{root}", str(root)) for part in template], root))
    return outcomes[0], outcomes[1]


# ---------------------------------------------------------------------------
# New project: `afs new` is the shortcut for `afs api new`
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("extra", [[], ["--dry-run"], ["--azd"], ["--python-version", "3.11"]])
def test_new_and_api_new_generate_the_same_output(tmp_path: Path, extra: list[str]) -> None:
    outcomes = []
    for label, command in (("a", ["new"]), ("b", ["api", "new"])):
        dest = tmp_path / label
        dest.mkdir()
        outcomes.append(
            _run([*command, "demo", "--destination", str(dest), "--no-git", *extra], dest)
        )

    assert outcomes[0][0] == outcomes[1][0] == 0
    assert outcomes[0] == outcomes[1]


def test_new_and_api_new_refuse_an_existing_directory_the_same_way(tmp_path: Path) -> None:
    outcomes = []
    for label, command in (("a", ["new"]), ("b", ["api", "new"])):
        dest = tmp_path / label
        (dest / "demo").mkdir(parents=True)
        (dest / "demo" / "keep.txt").write_text("keep", encoding="utf-8")
        outcomes.append(_run([*command, "demo", "--destination", str(dest), "--no-git"], dest))

    assert outcomes[0][0] != 0
    assert outcomes[0] == outcomes[1]
    assert outcomes[0][3] == {"demo/keep.txt": outcomes[0][3]["demo/keep.txt"]}


def test_new_and_api_new_expose_the_same_options() -> None:
    def options(args: list[str]) -> str:
        result = runner.invoke(app, [*args, "--help"])
        assert result.exit_code == 0
        # Drop the usage line and description: they name the command; the options must not differ.
        return result.stdout.split("Options")[1]

    assert options(["new"]) == options(["api", "new"])


def test_new_help_keeps_its_shortcut_description() -> None:
    help_text = " ".join(runner.invoke(app, ["new", "--help"]).stdout.split())
    assert "Create a new API project (shortcut for 'afs api new')." in help_text


# ---------------------------------------------------------------------------
# Listing: top-level and `advanced` listings, and the deprecated `profiles` alias
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("top", "advanced"), [("templates", "advanced templates"), ("presets", "advanced presets")]
)
def test_top_level_and_advanced_listings_are_identical(top: str, advanced: str) -> None:
    first = runner.invoke(app, top.split())
    second = runner.invoke(app, advanced.split())

    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout
    assert first.stdout.strip()
    assert first.stderr == second.stderr == ""


def test_profiles_is_presets_plus_a_deprecation_warning_on_stderr() -> None:
    presets = runner.invoke(app, ["presets"])
    profiles = runner.invoke(app, ["profiles"])

    assert profiles.exit_code == 0
    assert profiles.stdout == presets.stdout
    assert profiles.stderr == (
        "DeprecationWarning: The command 'profiles' is deprecated.\n"
        "warning: 'afs profiles' is deprecated and will be removed in a future release. "
        "Use: afs presets\n"
    )


def test_listing_commands_keep_their_help_text() -> None:
    assert (
        "List available scaffold templates." in runner.invoke(app, ["templates", "--help"]).stdout
    )
    assert "List available project presets." in runner.invoke(app, ["presets", "--help"]).stdout
    assert "List available scaffold templates." in (
        runner.invoke(app, ["advanced", "templates", "--help"]).stdout
    )
    assert "List available project presets." in (
        runner.invoke(app, ["advanced", "presets", "--help"]).stdout
    )


# ---------------------------------------------------------------------------
# Adding to an existing project
# ---------------------------------------------------------------------------


def test_api_add_and_advanced_add_http_write_the_same_files(tmp_path: Path) -> None:
    first, second = _equivalent(
        tmp_path,
        ["api", "add", "get-status", "--project-root", "{root}"],
        ["advanced", "add", "http", "get-status", "--project-root", "{root}"],
    )

    assert first[0] == 0
    assert first == second
    assert "Created function at <ROOT>" in first[1]


@pytest.mark.parametrize("dry_run", [[], ["--dry-run"]])
@pytest.mark.parametrize(("kind", "name"), [("add-route", "status"), ("add-resource", "products")])
def test_api_and_advanced_add_variants_are_identical(
    tmp_path: Path, kind: str, name: str, dry_run: list[str]
) -> None:
    first, second = _equivalent(
        tmp_path,
        ["api", kind, name, "--project-root", "{root}", *dry_run],
        ["advanced", kind, name, "--project-root", "{root}", *dry_run],
    )

    assert first[0] == 0
    assert first == second


@pytest.mark.parametrize(
    "args",
    [
        ["api", "add", "get-status"],
        ["advanced", "add", "http", "get-status"],
        ["api", "add-route", "status"],
        ["advanced", "add-route", "status"],
        ["api", "add-resource", "products"],
        ["advanced", "add-resource", "products"],
    ],
)
def test_add_commands_report_a_missing_project_with_exit_code_1(
    tmp_path: Path, args: list[str]
) -> None:
    missing = tmp_path / "not-a-project"
    missing.mkdir()
    result = runner.invoke(app, [*args, "--project-root", str(missing)])

    assert result.exit_code == 1
    assert result.stdout.strip()
    assert result.stderr == ""
    assert list(missing.iterdir()) == []


@pytest.mark.parametrize(
    "args", [["api", "add", "get-status"], ["advanced", "add", "http", "get-status"]]
)
def test_add_commands_refuse_to_overwrite_an_existing_function(
    tmp_path: Path, args: list[str]
) -> None:
    root = _project(tmp_path)
    assert runner.invoke(app, [*args, "--project-root", str(root)]).exit_code == 0
    before = _tree(root)

    again = runner.invoke(app, [*args, "--project-root", str(root)])

    assert again.exit_code == 1
    assert _tree(root) == before


# ---------------------------------------------------------------------------
# Deprecated `afs add`: its warning, output and error contract stay exactly as published
# ---------------------------------------------------------------------------


def test_legacy_add_http_contract(tmp_path: Path) -> None:
    root = _project(tmp_path)
    code, out, err, tree = _run(["add", "http", "get-status", "--project-root", str(root)], root)

    assert code == 0
    assert err == (
        "DeprecationWarning: The command 'add' is deprecated.\n"
        "warning: 'afs add' is deprecated and will be removed in a future release. "
        "Use: afs api add get-status --project-root <ROOT>\n"
    )
    assert out.startswith("Created: <ROOT>")
    assert out.count("\n") == 1
    reference = _project(tmp_path / "ref")
    runner.invoke(app, ["api", "add", "get-status", "--project-root", str(reference)])
    assert tree == _tree(reference)


def test_legacy_add_non_http_points_at_advanced_add(tmp_path: Path) -> None:
    root = _project(tmp_path)
    code, out, err, tree = _run(["add", "TIMER", "tick", "--project-root", str(root)], root)

    assert code == 0
    assert err == (
        "DeprecationWarning: The command 'add' is deprecated.\n"
        "warning: 'afs add' is deprecated and will be removed in a future release. "
        "Use: afs advanced add timer tick --project-root <ROOT>\n"
    )
    assert out.startswith("Created: <ROOT>")
    reference = _project(tmp_path / "ref")
    runner.invoke(app, ["advanced", "add", "timer", "tick", "--project-root", str(reference)])
    assert tree == _tree(reference)


def test_legacy_add_dry_run_previews_without_writing(tmp_path: Path) -> None:
    root = _project(tmp_path)
    before = _tree(root)
    code, out, err, tree = _run(
        ["add", "http", "get-status", "--project-root", str(root), "--dry-run"], root
    )
    modern = runner.invoke(
        app, ["api", "add", "get-status", "--project-root", str(root), "--dry-run"]
    )

    assert code == 0
    assert tree == before
    assert out == modern.stdout.replace(str(root), "<ROOT>")
    assert "warning: 'afs add' is deprecated" in err


def test_legacy_add_errors_go_to_stderr_with_exit_code_1(tmp_path: Path) -> None:
    missing = tmp_path / "not-a-project"
    missing.mkdir()
    code, out, err, _ = _run(["add", "http", "x", "--project-root", str(missing)], missing)

    assert code == 1
    assert out == ""
    lines = err.splitlines()
    assert lines[0] == "DeprecationWarning: The command 'add' is deprecated."
    assert lines[1].startswith("warning: 'afs add' is deprecated")
    assert lines[2].startswith("Error: ")
