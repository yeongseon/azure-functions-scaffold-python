from __future__ import annotations

from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import TemplateContext
from azure_functions_scaffold.template_registry import get_template


def scaffold_project(
    project_name: str,
    destination: Path,
    template_name: str = "http",
) -> Path:
    context = build_template_context(project_name)
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
        rendered_path = _render_path(relative_path, context)
        output_path = target_dir / rendered_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template_name = relative_path.as_posix()
        rendered_content = environment.get_template(template_name).render(
            project_name=context.project_name,
            project_slug=context.project_slug,
        )
        output_path.write_text(rendered_content, encoding="utf-8")

    return target_dir


def build_template_context(project_name: str) -> TemplateContext:
    normalized_name = validate_project_name(project_name)
    return TemplateContext(
        project_name=normalized_name,
        project_slug=_slugify(normalized_name),
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
