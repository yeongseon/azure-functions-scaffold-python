# Getting Started

Follow this guide to install the CLI and generate your first production-ready Azure Functions Python v2 project.

### Prerequisites

Ensure you have the following tools installed:

*   **Python 3.10+**: Supported versions are 3.10 through 3.14.
*   **pip**: Python package manager.
*   **Azure Functions Core Tools**: Required for local testing (`v4.x` recommended).

### Installation

Install the CLI globally or in a virtual environment. Use `pipx` if you want to keep your global environment clean.

```bash
# Global install
pip install azure-functions-scaffold

# Recommended (Isolated install)
pipx install azure-functions-scaffold
```

Verify the installation by running the command or its alias:

```bash
afs --version
```

### Create Your First Project

Run the `new` command to generate a standard HTTP project.

```bash
afs new my-api --preset standard
```

**Expected Output:**

```text
Created project at /path/to/my-api
```

### Run Locally

Install the generated dependencies and start the local runtime.

```bash
cd my-api
pip install -e .
func start
```

### Test the Endpoint

Once the local runtime is ready, use `curl` to test the default HTTP trigger.

```bash
curl "http://localhost:7071/api/hello?name=Azure"
```

**Expected Output:**

```text
Hello, Azure!
```

### What's Next?

Learn how the code is organized in the [Project Structure](project-structure.md) guide.
