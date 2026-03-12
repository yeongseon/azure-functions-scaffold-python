# Installation Guide

This page explains how to install and set up azure-functions-scaffold on your local machine. Follow these instructions to get started with the CLI tool.

## Prerequisites

Before installing azure-functions-scaffold, ensure your system meets these requirements:

- Python 3.10 or higher. The tool supports versions 3.10, 3.11, 3.12, 3.13, and 3.14.
- pip, which usually comes pre-installed with Python.
- No additional system-level dependencies are required for the CLI itself.
- For testing your generated projects, we recommend installing the Azure Functions Core Tools.

## Recommended Installation (PyPI)

The easiest way to install azure-functions-scaffold is through PyPI using pip.

```bash
pip install azure-functions-scaffold
```

## Verify Installation

Once the installation finishes, verify that the CLI is available by checking its version.

```bash
azure-functions-scaffold --version
```

Expected output:
```text
0.3.0
```

You can also verify that the package imports correctly from Python:

```bash
python -c "from azure_functions_scaffold import cli; print('OK')"
```

Expected output:

```text
OK
```

## Installation in a Virtual Environment

We recommend installing the tool within a virtual environment to keep your global Python installation clean and avoid dependency conflicts.

```bash
# Create a virtual environment
python -m venv .venv

# Activate the environment
# On Linux or macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Install the package
pip install azure-functions-scaffold
```

## Global Installation with pipx

If you want to use azure-functions-scaffold as a global CLI tool without managing virtual environments manually, use pipx.

```bash
pipx install azure-functions-scaffold
```

## Development Installation

If you want to contribute to the project or run the latest code from the repository, follow these steps for a development setup.

```bash
# Clone the repository
git clone https://github.com/yeongseon/azure-functions-scaffold.git

# Navigate to the project directory
cd azure-functions-scaffold

# Run the installation script
make install
```

This process creates a dedicated virtual environment, installs the Hatch build tool, and configures pre-commit hooks for development.

## Runtime Dependencies

The package is designed to be lightweight and relies on only two primary runtime dependencies:

- jinja2 (>=3.1, <4.0): The engine used for rendering project templates.
- typer (>=0.16, <1.0): The framework used for the CLI interface.

## Managing the Installation

### Upgrading the Package

To update azure-functions-scaffold to the latest version, run the following command:

```bash
pip install --upgrade azure-functions-scaffold
```

### Uninstalling the Package

If you need to remove the tool from your system, use pip:

```bash
pip uninstall azure-functions-scaffold
```

## Post-Installation: Creating Your First Project

After a successful installation, you can immediately start scaffolding new Azure Functions projects.

```bash
# Create a new project
azure-functions-scaffold new my-api

# Navigate to your new project
cd my-api
```

Refer to the CLI guide for a full list of commands and options.

## Troubleshooting

If you encounter issues during installation, check the following common solutions:

- Python version too old: Verify your version with `python --version`. Upgrade to at least 3.10.
- pip not found: If the pip command is missing, try running `python -m pip install azure-functions-scaffold`.
- Permission denied: Use a virtual environment or add the `--user` flag to your pip install command.
- Command not found: Ensure your Python scripts directory is in your system PATH after installation.
