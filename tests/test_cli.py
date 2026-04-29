"""Tests for top-level CLI commands (templates, presets, version) and entry point.

Intent-specific command tests live in test_cli_intents.py.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold import __version__, cli
from azure_functions_scaffold.cli import app

runner = CliRunner()


def test_templates_command_lists_available_templates() -> None:
    result = runner.invoke(app, ["templates"])

    assert result.exit_code == 0
    assert "http: HTTP-trigger Azure Functions Python v2 application." in result.stdout
    assert "timer: Timer-trigger Azure Functions Python v2 application." in result.stdout
    assert "queue: Queue-trigger Azure Functions Python v2 application." in result.stdout
    assert "blob: Blob-trigger Azure Functions Python v2 application." in result.stdout
    assert "servicebus: Service Bus-trigger Azure Functions Python v2 application." in result.stdout
    assert "eventhub: EventHub-trigger Azure Functions Python v2 application." in result.stdout
    assert "cosmosdb: CosmosDB-trigger Azure Functions Python v2 application." in result.stdout
    assert "durable: Durable Functions Azure Functions Python v2 application." in result.stdout
    assert "ai: AI/Azure OpenAI Azure Functions Python v2 application." in result.stdout
    assert "langgraph: LangGraph agent deployment on Azure Functions Python v2." in result.stdout


def test_presets_command_lists_available_presets() -> None:
    result = runner.invoke(app, ["presets"])

    assert result.exit_code == 0
    assert "minimal: Minimal Azure Functions project" in result.stdout
    assert "strict: Azure Functions project with Ruff, mypy, and pytest defaults." in result.stdout


def test_cli_with_no_args_prints_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Generate opinionated Azure Functions" in result.stdout
    assert "api" in result.stdout
    assert "worker" in result.stdout
    assert "ai" in result.stdout
    assert "advanced" in result.stdout


def test_version_option_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_main_invokes_typer_app(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def fake_app() -> None:
        called["value"] = True

    monkeypatch.setattr(cli, "app", fake_app)

    cli.main()

    assert called["value"] is True
