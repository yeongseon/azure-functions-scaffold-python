# Quick Start

This guide walks through creating and running your first Azure Functions Python v2
project with `azure-functions-scaffold` in about three minutes.

## Prerequisites

- Python 3.10+
- `pip`
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)

Optional for queue/blob template testing:

- Azurite (for local Azure Storage emulation)

## Step 1: Install

Install the CLI:

```bash
pip install azure-functions-scaffold
```

Verify the installation:

```bash
azure-functions-scaffold --version
```

Expected output:

```text
0.3.0
```

If the command is not found, re-open your terminal so the installed scripts path
is reloaded.

## Step 2: Create a Project

Generate a new HTTP-based project:

```bash
azure-functions-scaffold new my-api
```

Expected terminal output:

```text
Created project at ./my-api
```

The default template is `http`, so `--template http` is optional.

Generated tree:

```text
my-api/
|- function_app.py
|- host.json
|- local.settings.json.example
|- pyproject.toml
|- .gitignore
|- .funcignore
|- README.md
|- app/
|  |- core/
|  |  `- logging.py
|  |- functions/
|  |  `- http.py
|  |- schemas/
|  |  `- request_models.py
|  `- services/
|     `- hello_service.py
`- tests/
   `- test_http.py
```

## Step 3: Install Dependencies and Run

Move into the project, install dependencies, and start the local runtime:

```bash
cd my-api
pip install -e .
func start
```

Keep this terminal running while you test the endpoint.

Expected output:

```text
Azure Functions Core Tools
...
Functions:
        hello: [GET] http://localhost:7071/api/hello
```

## Step 4: Test It

Call the generated endpoint:

```bash
curl "http://localhost:7071/api/hello?name=Azure"
# Response: Hello, Azure!
```

## Step 5: Deploy

Publish to an Azure Function App:

```bash
func azure functionapp publish <YOUR_APP_NAME>
```

Replace `<YOUR_APP_NAME>` with an existing Function App name in your Azure
subscription.

## What's Next

- Try other templates: `--template timer`, `--template queue`
- Add features: `--with-openapi`, `--with-validation`
- Interactive mode: `--interactive`
- Full CLI reference: [`cli.md`](cli.md)
- Why this project structure: [`why.md`](why.md)

For a deeper understanding of generated files, continue to
[`template_spec.md`](template_spec.md).
