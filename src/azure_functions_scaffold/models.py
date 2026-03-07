from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateContext:
    project_name: str
    project_slug: str


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    description: str
    root: Path
