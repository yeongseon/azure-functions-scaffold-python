# Deploy to Azure

This guide walks you through deploying a scaffolded Azure Functions project to Azure, **step by step**.
No Azure experience required — every command is explained and copy-paste ready.

## Who this guide is for

You know Python and pip. You have used the `afs` CLI to scaffold a project locally (see [README](https://github.com/yeongseon/azure-functions-scaffold/blob/main/README.md)).
Now you want to deploy it to Azure so it runs in the cloud. This guide assumes you have **never used Azure before**.

## What you are deploying

`azure-functions-scaffold` generates ready-to-deploy Azure Functions projects from templates.
This guide deploys two templates:

- **`http` template** — An HTTP API with a `/api/hello` endpoint
- **`timer` template** — A scheduled background job that runs every 5 minutes

After following this guide, your scaffolded project will be running on Azure and reachable from the internet.

## Azure concepts you need for this guide

> New to Azure? Read [Choose an Azure Functions Hosting Plan](choose-a-plan.md) for a visual decision tree and plan comparison.

| Term | What it means |
|---|---|
| **Function App** | Your deployed application. Like a Flask/FastAPI app running in the cloud. |
| **Hosting plan** | Controls how your app scales, how fast it responds, and how much it costs. |
| **Resource Group** | A folder for Azure resources. Delete it to clean up everything at once. |
| **Storage Account** | Required by Azure Functions for internal state. You create one and hand it to the Function App. |

## Recommended plan for this repo

| | |
|---|---|
| **Default plan** | Flex Consumption |
| **Why** | Scaffold generates lightweight HTTP APIs and timer jobs. Flex Consumption is the cheapest option with zero idle cost and 30-minute timeout — more than enough for scaffolded projects. |
| **Switch to Premium if** | You add heavy dependencies (>500 MB) or need sub-second cold starts. |

## Before you start

| Requirement | How to check | Install if missing |
|---|---|---|
| Azure account | [portal.azure.com](https://portal.azure.com) | [Create free account](https://azure.microsoft.com/free/) |
| Azure CLI | `az --version` | [Install Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) |
| Azure Functions Core Tools v4 | `func --version` | [Install Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools) |
| Python 3.10–3.13 | `python --version` | [python.org](https://www.python.org/downloads/) |
| `afs` CLI installed | `afs --version` | `pip install azure-functions-scaffold` |
| Local project working | `func start` → responds to `curl` | See [README Quick Start](https://github.com/yeongseon/azure-functions-scaffold/blob/main/README.md) |

> ⚠️ **Verify locally first.** If your project doesn't work locally, it won't work on Azure either.

## Read these warnings before provisioning

1. **Storage account names must be globally unique** across all of Azure. Use a name like `stmyapp` + a random suffix. Only lowercase letters and numbers, 3–24 characters.
2. **Use one region for all resources.** Mixing regions adds latency and can cause failures.
3. **Local `.env` values don't automatically appear on Azure.** You must set app settings separately via `az functionapp config appsettings set`.
4. **First deploy takes longer than expected.** Azure runs a remote build to install your Python dependencies. Wait for the "Deployment successful" message before testing.
5. **Deleting local files does not delete Azure resources.** You must explicitly delete the resource group to stop billing (see [Clean up resources](#clean-up-resources)).

---

## Example 1: Deploy HTTP API (`http` template)

### Step 1 — Scaffold the project

```bash
afs new my-http-api --template http --dry-run
```

This shows what files will be created **without writing anything**:

```text
Dry run: create project at <CURRENT_DIR>/my-http-api
Template: http
Preset: standard
Python: 3.10
Files:
  - .funcignore
  - .gitignore
  - Makefile
  - README.md
  - app/__init__.py
  - app/core/__init__.py
  - app/core/logging.py
  - app/functions/__init__.py
  - app/functions/http.py
  - app/schemas/__init__.py
  - app/schemas/request_models.py
  - app/services/__init__.py
  - app/services/hello_service.py
  - function_app.py
  - host.json
  - local.settings.json.example
  - pyproject.toml
  - tests/test_http.py
```

Now create the actual project:

```bash
afs new my-http-api --template http
cd my-http-api
```

### Step 2 — Create `requirements.txt`

Azure Functions expects a `requirements.txt` file in the project root:

```bash
cat > requirements.txt << 'EOF'
azure-functions>=1.23.0
azure-functions-logging>=0.2.0
EOF
```

### Step 3 — Verify locally

```bash
cp local.settings.json.example local.settings.json
func start
```

In another terminal:

```bash
curl http://localhost:7071/api/hello?name=Local
```

Expected output:

```text
Hello, Local!
```

Stop the local server with `Ctrl+C` before deploying.

### Step 4 — Sign in to Azure

```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
```

> **How to find your subscription ID**: Run `az account list --output table` and look for the `SubscriptionId` column.

### Step 5 — Set shell variables

```bash
RESOURCE_GROUP="rg-scaffold-http"
LOCATION="koreacentral"
STORAGE_ACCOUNT="stscaffoldhttp$(date +%s | tail -c 6)"
FUNCTIONAPP_NAME="func-scaffold-http"
```

> Replace `koreacentral` with a region close to you. Run `az functionapp list-flexconsumption-locations -o table` to see available Flex Consumption regions.

### Step 6 — Create a resource group

```bash
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
```

Output:

```json
{
  "location": "koreacentral",
  "name": "rg-scaffold-http",
  "properties": {
    "provisioningState": "Succeeded"
  }
}
```

### Step 7 — Create a storage account

```bash
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS
```

> This takes about 10 seconds. Look for `"provisioningState": "Succeeded"` in the output.

### Step 8 — Create the Function App (Flex Consumption)

```bash
az functionapp create \
  --name "$FUNCTIONAPP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --flexconsumption-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11
```

Output includes:

```text
Application Insights "<FUNCTIONAPP_NAME>" was created for this Function App.
```

> Azure automatically creates an Application Insights resource for monitoring. You can use it later to view logs and traces.

### Step 9 — Deploy the code

```bash
func azure functionapp publish "$FUNCTIONAPP_NAME"
```

Output:

```text
Getting site publishing info...
Starting the function app deployment...
Creating archive for current directory...
Performing remote build for functions project.
...
Deployment completed successfully.
Functions in func-scaffold-http:
    hello - [httpTrigger]
        Invoke url: https://func-scaffold-http.azurewebsites.net/api/hello
```

> ⚠️ **First deploy may take 1–3 minutes** because Azure installs your Python dependencies via remote build.

### Step 10 — Verify on Azure

```bash
curl "https://$FUNCTIONAPP_NAME.azurewebsites.net/api/hello"
```

Expected output:

```text
Hello, world!
```

Try with a name parameter:

```bash
curl "https://$FUNCTIONAPP_NAME.azurewebsites.net/api/hello?name=Azure"
```

Expected output:

```text
Hello, Azure!
```

✅ **Your scaffolded HTTP API is now running on Azure!**

---

## Example 2: Deploy Timer Job (`timer` template)

### Step 1 — Scaffold the project

```bash
afs new my-timer-job --template timer --dry-run
```

Output:

```text
Dry run: create project at <CURRENT_DIR>/my-timer-job
Template: timer
Preset: standard
Python: 3.10
Files:
  - .funcignore
  - .gitignore
  - Makefile
  - README.md
  - app/__init__.py
  - app/core/__init__.py
  - app/core/logging.py
  - app/functions/__init__.py
  - app/functions/timer.py
  - app/services/__init__.py
  - app/services/maintenance_service.py
  - function_app.py
  - host.json
  - local.settings.json.example
  - pyproject.toml
  - tests/test_timer.py
```

Create the actual project:

```bash
afs new my-timer-job --template timer
cd my-timer-job
```

### Step 2 — Create `requirements.txt`

```bash
cat > requirements.txt << 'EOF'
azure-functions>=1.23.0
azure-functions-logging>=0.2.0
EOF
```

### Step 3 — Set shell variables

```bash
RESOURCE_GROUP="rg-scaffold-timer"
LOCATION="koreacentral"
STORAGE_ACCOUNT="stscaffoldtimer$(date +%s | tail -c 6)"
FUNCTIONAPP_NAME="func-scaffold-timer"
```

### Step 4 — Create Azure resources

```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS

az functionapp create \
  --name "$FUNCTIONAPP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --flexconsumption-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11
```

### Step 5 — Deploy the code

```bash
func azure functionapp publish "$FUNCTIONAPP_NAME"
```

Output:

```text
Functions in func-scaffold-timer:
    cleanup - [timerTrigger]
```

### Step 6 — Verify timer execution

Timer triggers don't have HTTP endpoints. Verify by watching the live log stream:

```bash
func azure functionapp logstream "$FUNCTIONAPP_NAME"
```

Wait for the next scheduled execution (default: every 5 minutes). You should see:

```text
Executing 'Functions.cleanup' (Reason='Timer fired at 2026-04-06T14:00:00.0000000+00:00')
Timer trigger executed.
Executed 'Functions.cleanup' (Succeeded, Duration=7ms)
```

Press `Ctrl+C` to stop the log stream.

> ⚠️ **Timer schedule uses UTC.** The default schedule `0 */5 * * * *` runs every 5 minutes in UTC, not your local timezone.

✅ **Your scaffolded timer job is now running on Azure!**

---

## If you need a different plan

The examples above use **Flex Consumption**. If you need a different plan, only the Function App creation command changes — everything else stays the same.

See [Choose an Azure Functions Hosting Plan](choose-a-plan.md) for complete per-plan commands with copy-paste blocks.

### Premium (EP1) — for faster cold starts

Replace the `az functionapp create` step with:

```bash
# Create the Premium plan
az functionapp plan create \
  --name "${FUNCTIONAPP_NAME}-plan" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku EP1 \
  --is-linux

# Create the Function App on that plan
az functionapp create \
  --name "$FUNCTIONAPP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --plan "${FUNCTIONAPP_NAME}-plan" \
  --runtime python \
  --runtime-version 3.11 \
  --os-type Linux
```

### Dedicated (B1) — for fixed-cost hosting

Replace the `az functionapp create` step with:

```bash
# Create the App Service plan
az appservice plan create \
  --name "${FUNCTIONAPP_NAME}-plan" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku B1 \
  --is-linux

# Create the Function App on that plan
az functionapp create \
  --name "$FUNCTIONAPP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --plan "${FUNCTIONAPP_NAME}-plan" \
  --runtime python \
  --runtime-version 3.11 \
  --os-type Linux
```

---

## Troubleshooting

### Provisioning failed

| Symptom | Usually means | How to fix |
|---|---|---|
| `StorageAccountAlreadyTaken` | Storage account name is not globally unique | Add a random suffix: `stmyapp$(date +%s \| tail -c 6)` |
| `LocationNotAvailableForResourceType` | Flex Consumption not available in your region | Run `az functionapp list-flexconsumption-locations -o table` and pick a different region |
| `SubscriptionNotFound` | Wrong subscription selected | Run `az account list -o table` and `az account set --subscription <ID>` |

### Deployment failed

| Symptom | Usually means | How to fix |
|---|---|---|
| `ModuleNotFoundError` in deployment logs | Missing `requirements.txt` or wrong Python version | Ensure `requirements.txt` is in the project root and matches your Function App's Python version |
| Deployment hangs for >5 minutes | Remote build is slow (common on B1 Dedicated plans) | Wait. First deploy takes longer. If it times out, retry `func azure functionapp publish` |
| `Can't find app with name` | Function App not fully provisioned yet | Wait 30 seconds and retry |

### The app deployed but does not behave correctly

| Symptom | Usually means | How to fix |
|---|---|---|
| HTTP 404 on `/api/hello` | Function not registered | Check `func azure functionapp publish` output — it should list `hello - [httpTrigger]` |
| Timer never fires | Schedule syntax or timezone issue | Timer uses NCRONTAB format in UTC. Check `function.json` or decorator schedule. |
| `Internal Server Error` (500) | Python exception in your code | Check logs: `func azure functionapp logstream "$FUNCTIONAPP_NAME"` |

### Logs and monitoring

```bash
# Live log stream (real-time)
func azure functionapp logstream "$FUNCTIONAPP_NAME"

# Recent invocations via Application Insights
az monitor app-insights events show \
  --app "$FUNCTIONAPP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --type requests \
  --offset 1h
```

### Before opening an issue

If you're stuck, please include the following when opening an issue:

```bash
# 1. Azure CLI version
az --version

# 2. Functions Core Tools version
func --version

# 3. Python version
python --version

# 4. afs version
afs --version

# 5. Function App status
az functionapp show --name "$FUNCTIONAPP_NAME" --resource-group "$RESOURCE_GROUP" --query "{state:state, runtimeVersion:siteConfig.linuxFxVersion}"

# 6. Recent logs
func azure functionapp logstream "$FUNCTIONAPP_NAME"
```

---

## Clean up resources

> ⚠️ **Azure resources cost money until deleted.** Always clean up after testing.

Delete each resource group to remove **all** resources inside it:

```bash
# Delete HTTP example resources
az group delete --name "rg-scaffold-http" --yes --no-wait

# Delete Timer example resources
az group delete --name "rg-scaffold-timer" --yes --no-wait
```

The `--no-wait` flag returns immediately. Deletion happens in the background and takes 1–2 minutes.

To verify deletion:

```bash
az group list --query "[?starts_with(name, 'rg-scaffold')]" -o table
```

---

## Sources

- [Azure Functions Python quickstart](https://learn.microsoft.com/azure/azure-functions/create-first-function-cli-python) — Official getting-started guide
- [Azure Functions Core Tools reference](https://learn.microsoft.com/azure/azure-functions/functions-core-tools-reference) — CLI command reference
- [Azure Functions app settings](https://learn.microsoft.com/azure/azure-functions/functions-how-to-use-azure-function-app-settings) — Environment variables and configuration
- [Azure Functions timer trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer) — Timer schedule format and options
- [Azure Functions hosting plans](https://learn.microsoft.com/azure/azure-functions/functions-scale) — Plan comparison and limits
- [Flex Consumption plan](https://learn.microsoft.com/azure/azure-functions/flex-consumption-plan) — Flex Consumption details

## See Also

- [Choose an Azure Functions Hosting Plan](choose-a-plan.md) — Plan selection guide with decision tree
- [Deploying guide](./guide/deploying.md) — Additional deployment topics
- [`azure-functions-openapi`](https://github.com/yeongseon/azure-functions-openapi)
- [`azure-functions-validation`](https://github.com/yeongseon/azure-functions-validation)
- [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor)
- [`azure-functions-logging`](https://github.com/yeongseon/azure-functions-logging)
- [`azure-functions-langgraph`](https://github.com/yeongseon/azure-functions-langgraph)
