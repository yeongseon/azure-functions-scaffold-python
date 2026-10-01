# Deploying

> For a comprehensive step-by-step deployment walkthrough with examples, see [Deployment Guide](../deployment.md).

Once your project is ready for production, follow these steps to deploy it to Azure.

### Pre-deployment Checklist

Before deploying, ensure you have:

*   **App Settings**: Created an Azure Function App with the correct Python version (3.10-3.13 GA, 3.14 Preview). Verify Preview support for your region and hosting plan before using 3.14.
*   **Host.json**: Verified that `host.json` contains any necessary production configurations.
*   **Tests**: Run your Pytest suite locally and passed all checks.
*   **Local Run**: Successfully started the runtime locally using `func start`.

### Deploy Command

Use the Azure Functions Core Tools to publish your project.

```bash
# Authenticate if necessary
az login

# Deploy the project
func azure functionapp publish <YOUR_APP_NAME>
```

**Expected Output:**

```text
Getting site publishing info...
Uploading package...
Deployment completed successfully.
Remote build completed!
```

### Production Settings

Keep your `local.settings.json` separate from production settings. Configure secrets and connection strings (like `SERVICEBUS_CONNECTION` or `AzureWebJobsStorage`) in the Azure Portal or using the CLI:

```bash
az functionapp config appsettings set --name <APP_NAME> --resource-group <RG_NAME> --settings "CONNECTION_STRING=your_value"
```

### GitHub Actions

If you used the `--github-actions` flag during generation, a `.github/workflows/main_azure_function.yml` file was created. You can use this for automated deployments.

1.  Commit and push your code to GitHub.
2.  Set up the `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` secret in your repository settings.
3.  The workflow will automatically build and deploy on every push to the `main` branch.

### What's Next?

Encountered an issue? Check the [Troubleshooting](troubleshooting.md) guide.
