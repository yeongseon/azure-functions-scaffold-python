from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess  # nosec B404

from jinja2 import Environment, FileSystemLoader, select_autoescape

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import ProjectOptions, TemplateContext
from azure_functions_scaffold.template_registry import build_project_options, get_template


def scaffold_project(
    project_name: str,
    destination: Path,
    template_name: str = "http",
    options: ProjectOptions | None = None,
) -> Path:
    resolved_options = options or build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
    )
    context = build_template_context(project_name, resolved_options)
    target_dir = resolve_target_dir(destination=destination, project_name=context.project_name)
    if target_dir.exists():
        raise ScaffoldError(f"Target directory already exists: {target_dir}")

    template = get_template(template_name)
    template_root = template.root
    environment = Environment(
        loader=FileSystemLoader(str(template_root)),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml"),
            default_for_string=False,
            default=False,
        ),
        keep_trailing_newline=True,
    )

    target_dir.mkdir(parents=True, exist_ok=False)

    for template_path in _iter_template_files(template_root):
        relative_path = template_path.relative_to(template_root)
        if not _should_render_template(relative_path, context):
            continue
        rendered_path = _render_path(relative_path, context)
        output_path = target_dir / rendered_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template_rel_name = relative_path.as_posix()
        rendered_content = environment.get_template(template_rel_name).render(
            project_name=context.project_name,
            project_slug=context.project_slug,
            python_version=context.python_version,
            python_upper_bound=context.python_upper_bound,
            preset_name=context.preset_name,
            include_github_actions=context.include_github_actions,
            include_ruff=context.include_ruff,
            include_mypy=context.include_mypy,
            include_pytest=context.include_pytest,
        )
        output_path.write_text(rendered_content, encoding="utf-8")

    if context.initialize_git:
        _initialize_git_repository(target_dir)

    return target_dir


def describe_scaffold_project(
    project_name: str,
    destination: Path,
    template_name: str = "http",
    options: ProjectOptions | None = None,
) -> list[str]:
    resolved_options = options or build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
    )
    context = build_template_context(project_name, resolved_options)
    target_dir = resolve_target_dir(destination=destination, project_name=context.project_name)
    template = get_template(template_name)

    lines = [
        f"Dry run: create project at {target_dir}",
        f"Template: {template.name}",
        f"Preset: {context.preset_name}",
        f"Python: {context.python_version}",
    ]
    if context.include_github_actions:
        lines.append("GitHub Actions: enabled")
    if context.initialize_git:
        lines.append("Git initialization: enabled")

    lines.append("Files:")
    for template_path in _iter_template_files(template.root):
        relative_path = template_path.relative_to(template.root)
        if not _should_render_template(relative_path, context):
            continue
        rendered_path = _render_path(relative_path, context)
        lines.append(f"  - {rendered_path.as_posix()}")

    return lines


def build_template_context(project_name: str, options: ProjectOptions) -> TemplateContext:
    normalized_name = validate_project_name(project_name)
    python_version = options.python_version
    return TemplateContext(
        project_name=normalized_name,
        project_slug=_slugify(normalized_name),
        python_version=python_version,
        python_upper_bound=_next_python_minor(python_version),
        preset_name=options.preset_name,
        include_github_actions=options.include_github_actions,
        initialize_git=options.initialize_git,
        include_ruff="ruff" in options.tooling,
        include_mypy="mypy" in options.tooling,
        include_pytest="pytest" in options.tooling,
    )


def validate_project_name(project_name: str) -> str:
    normalized_name = project_name.strip()
    if not normalized_name:
        raise ScaffoldError("Project name must not be empty.")

    if normalized_name in {".", ".."}:
        raise ScaffoldError("Project name must be a normal directory name.")

    if "/" in normalized_name or "\\" in normalized_name:
        raise ScaffoldError("Project name must not contain path separators.")

    if normalized_name.startswith("-"):
        raise ScaffoldError("Project name must not start with '-'.")

    return normalized_name


def resolve_target_dir(destination: Path, project_name: str) -> Path:
    if destination.exists() and not destination.is_dir():
        raise ScaffoldError(f"Destination must be a directory: {destination}")
    return destination / project_name


def _iter_template_files(template_root: Path) -> list[Path]:
    return sorted(path for path in template_root.rglob("*") if path.is_file())


def _should_render_template(relative_path: Path, context: TemplateContext) -> bool:
    if relative_path.parts[0] == ".github" and not context.include_github_actions:
        return False

    if relative_path.parts[0] == "tests" and not context.include_pytest:
        return False

    return True


def _render_path(relative_path: Path, context: TemplateContext) -> Path:
    rendered_parts: list[str] = []
    for part in relative_path.parts:
        rendered = part.replace("__project_name__", _slugify(context.project_name))
        if rendered.endswith(".j2"):
            rendered = rendered[:-3]
        rendered_parts.append(rendered)
    return Path(*rendered_parts)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "azure-functions-app"


def _next_python_minor(python_version: str) -> str:
    major, minor = python_version.split(".", maxsplit=1)
    return f"{major}.{int(minor) + 1}"


def _initialize_git_repository(project_root: Path) -> None:
    git_executable = shutil.which("git")
    if not git_executable:
        raise ScaffoldError("Git is not installed or not available on PATH.")

    try:
        subprocess.run(
            [git_executable, "init"],  # nosec B603
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ScaffoldError("Git is not installed or not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or "git init failed"
        raise ScaffoldError(f"Failed to initialize a git repository: {stderr}") from exc
