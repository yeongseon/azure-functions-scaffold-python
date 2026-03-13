# Expanding Your Project

The `add` command allows you to add new triggers to an existing project while maintaining the Blueprint structure. It automatically handles trigger registration in `function_app.py`.

### The `add` Command

Use the `add` command to append new function modules to your project root.

```bash
afs add <trigger-type> <function-name> --project-root <path>
```

When you run this command, the CLI:
1. Creates a new Blueprint file in `app/functions/`.
2. Creates a unit test in `tests/`.
3. Imports and registers the new Blueprint in `function_app.py`.

### Examples

Add a secondary HTTP endpoint to your API:
```bash
afs add http user-profile
```

Add a timer trigger to an existing project:
```bash
afs add timer cleanup-job
```

Add a queue listener to handle background tasks:
```bash
afs add queue task-processor
```

### Dry Run

Use the `--dry-run` flag to preview which files will be created and how `function_app.py` will be modified before making any changes.

```bash
afs add http reports --dry-run
```

### Development Workflow

1.  **Add Trigger**: Run the `add` command to generate the boilerplate.
2.  **Implement Logic**: Create a corresponding service file in `app/services/` and write your core business rules there.
3.  **Update Schemas**: If needed, define new request/response models in `app/schemas/`.
4.  **Add Tests**: Update the generated test file in `tests/` to verify your new function.

### What's Next?

Once your project is ready, follow the [Deploying](deploying.md) guide to push it to Azure.
