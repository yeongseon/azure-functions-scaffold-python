from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateContext:
    project_name: str
    project_slug: str
    python_version: str
    python_upper_bound: str
    preset_name: str
    include_github_actions: bool
    initialize_git: bool
    include_ruff: bool
    include_mypy: bool
    include_pytest: bool
    include_openapi: bool
    include_validation: bool


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    description: str
    root: Path


@dataclass(frozen=True)
class PresetSpec:
    name: str
    description: str
    tooling: tuple[str, ...]


@dataclass(frozen=True)
class ProjectOptions:
    preset_name: str
    python_version: str
    tooling: tuple[str, ...]
    include_github_actions: bool
    initialize_git: bool
    include_openapi: bool
    include_validation: bool
