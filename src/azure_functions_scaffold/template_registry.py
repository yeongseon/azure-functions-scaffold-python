from __future__ import annotations

from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import TemplateSpec

TEMPLATE_ROOT = Path(__file__).parent / "templates"


def list_templates() -> list[TemplateSpec]:
    return [
        TemplateSpec(
            name="http",
            description="HTTP-trigger Azure Functions Python v2 application.",
            root=TEMPLATE_ROOT / "http",
        )
    ]


def get_template(name: str) -> TemplateSpec:
    normalized_name = name.strip().lower()
    for template in list_templates():
        if template.name == normalized_name:
            return template

    available = ", ".join(template.name for template in list_templates())
    raise ScaffoldError(f"Unknown template '{name}'. Available templates: {available}")
