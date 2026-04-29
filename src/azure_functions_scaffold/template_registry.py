from __future__ import annotations

from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import IntentSpec, PresetSpec, ProjectOptions, TemplateSpec

TEMPLATE_ROOT = Path(__file__).parent / "templates"
SUPPORTED_PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
PREVIEW_PYTHON_VERSIONS: frozenset[str] = frozenset({"3.14"})
SUPPORTED_TOOLING = ("ruff", "mypy", "pytest")
TEMPLATE_SPECS = (
    TemplateSpec(
        name="http",
        description="HTTP-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "http",
    ),
    TemplateSpec(
        name="timer",
        description="Timer-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "timer",
    ),
    TemplateSpec(
        name="queue",
        description="Queue-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "queue",
    ),
    TemplateSpec(
        name="blob",
        description="Blob-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "blob",
    ),
    TemplateSpec(
        name="servicebus",
        description="Service Bus-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "servicebus",
    ),
    TemplateSpec(
        name="eventhub",
        description="EventHub-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "eventhub",
    ),
    TemplateSpec(
        name="cosmosdb",
        description="CosmosDB-trigger Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "cosmosdb",
    ),
    TemplateSpec(
        name="durable",
        description="Durable Functions Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "durable",
    ),
    TemplateSpec(
        name="ai",
        description="AI/Azure OpenAI Azure Functions Python v2 application.",
        root=TEMPLATE_ROOT / "ai",
    ),
    TemplateSpec(
        name="langgraph",
        description="LangGraph agent deployment on Azure Functions Python v2.",
        root=TEMPLATE_ROOT / "langgraph",
    ),
)
PRESET_SPECS = (
    PresetSpec(
        name="minimal",
        description="Minimal Azure Functions project with no additional quality tooling.",
        tooling=(),
    ),
    PresetSpec(
        name="standard",
        description="Azure Functions project with Ruff and pytest defaults.",
        tooling=("ruff", "pytest"),
    ),
    PresetSpec(
        name="strict",
        description="Azure Functions project with Ruff, mypy, and pytest defaults.",
        tooling=("ruff", "mypy", "pytest"),
    ),
)
INTENT_SPECS: dict[str, IntentSpec] = {
    "api/new": IntentSpec(
        template="http",
        preset="strict",
        features=frozenset({"openapi", "validation", "doctor"}),
    ),
    "worker/timer": IntentSpec(template="timer", preset="standard"),
    "worker/queue": IntentSpec(template="queue", preset="standard"),
    "worker/blob": IntentSpec(template="blob", preset="standard"),
    "worker/servicebus": IntentSpec(template="servicebus", preset="standard"),
    "worker/eventhub": IntentSpec(template="eventhub", preset="standard"),
    "ai/agent": IntentSpec(template="langgraph", preset="standard"),
}


def list_templates() -> list[TemplateSpec]:
    return list(TEMPLATE_SPECS)


def get_template(name: str) -> TemplateSpec:
    normalized_name = name.strip().lower()
    for template in list_templates():
        if template.name == normalized_name:
            return template

    available = ", ".join(template.name for template in list_templates())
    raise ScaffoldError(f"Unknown template '{name}'. Available templates: {available}")


def list_presets() -> list[PresetSpec]:
    return list(PRESET_SPECS)


def get_preset(name: str) -> PresetSpec:
    normalized_name = name.strip().lower()
    for preset in list_presets():
        if preset.name == normalized_name:
            return preset

    available = ", ".join(preset.name for preset in list_presets())
    raise ScaffoldError(f"Unknown preset '{name}'. Available presets: {available}")


def build_project_options(
    *,
    preset_name: str,
    python_version: str,
    include_github_actions: bool,
    initialize_git: bool,
    tooling: tuple[str, ...] | None = None,
    include_openapi: bool = False,
    include_validation: bool = False,
    include_doctor: bool = False,
    include_azd: bool = False,
) -> ProjectOptions:
    preset = get_preset(preset_name)
    validate_python_version(python_version)
    resolved_tooling = validate_tooling(tooling or preset.tooling)
    resolved_preset_name = preset.name if resolved_tooling == preset.tooling else "custom"
    return ProjectOptions(
        preset_name=resolved_preset_name,
        python_version=python_version,
        tooling=resolved_tooling,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_openapi=include_openapi,
        include_validation=include_validation,
        include_doctor=include_doctor,
        include_azd=include_azd,
    )


def validate_python_version(python_version: str) -> str:
    normalized_version = python_version.strip()
    if normalized_version not in SUPPORTED_PYTHON_VERSIONS:
        available = ", ".join(SUPPORTED_PYTHON_VERSIONS)
        raise ScaffoldError(
            f"Unsupported Python version '{python_version}'. Supported versions: {available}"
        )
    return normalized_version


def is_preview_python(version: str) -> bool:
    """Return True if the given Python version is Preview on Azure Functions."""
    return version in PREVIEW_PYTHON_VERSIONS


def validate_tooling(tooling: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(item.strip().lower() for item in tooling if item.strip()))
    invalid = [item for item in normalized if item not in SUPPORTED_TOOLING]
    if invalid:
        available = ", ".join(SUPPORTED_TOOLING)
        invalid_list = ", ".join(invalid)
        raise ScaffoldError(
            f"Unsupported tooling selection '{invalid_list}'. Supported tooling: {available}"
        )
    return normalized
