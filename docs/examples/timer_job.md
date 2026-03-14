# Timer Job Example

This walkthrough creates a scheduled Azure Functions project, explains NCRONTAB
expressions, and sets up local storage emulation with Azurite.

## What You Will Build

You will create a timer-driven job that:

- runs on a schedule
- logs execution details
- is testable with pytest
- runs locally with Core Tools and Azurite

## 1) Generate a Timer Project

```bash
afs new nightly-maintenance --template timer --preset standard
```

Set up environment and dependencies:

```bash
cd nightly-maintenance
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run quality checks:

```bash
make check-all
```

## 2) Understand Timer Trigger Defaults

The generated timer function usually looks like this:

```python
@timer_blueprint.timer_trigger(
    arg_name="timer",
    schedule="0 */5 * * * *",
    run_on_startup=False,
    use_monitor=True,
)
def cleanup(timer: func.TimerRequest) -> None:
    ...
```

Default schedule `0 */5 * * * *` means every 5 minutes.

!!! note "Six-field NCRONTAB"
    Azure Functions uses NCRONTAB with six fields:
    `{second} {minute} {hour} {day} {month} {day-of-week}`.

## 3) NCRONTAB Quick Reference

| Expression | Meaning |
| :--- | :--- |
| `0 */5 * * * *` | Every 5 minutes |
| `0 0 * * * *` | Every hour (at minute 0) |
| `0 30 2 * * *` | Daily at 02:30 |
| `0 0 9 * * 1-5` | Weekdays at 09:00 |
| `0 0 0 1 * *` | First day of each month at midnight |

To run every day at 01:15, update schedule:

```python
schedule="0 15 1 * * *"
```

!!! warning "Avoid over-triggering in local dev"
    Start with an infrequent schedule while developing. A schedule like
    `*/5 * * * * *` fires every 5 seconds and can flood logs.

## 4) Azurite Setup for Local Development

Timer projects include `AzureWebJobsStorage=UseDevelopmentStorage=true` in
`local.settings.json.example`. That connection string expects Azurite locally.

Using npm package:

```bash
npm install -g azurite
azurite --silent --location .azurite --debug .azurite/debug.log
```

Using Docker:

```bash
docker run --rm -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite
```

Create active local settings file:

```bash
cp local.settings.json.example local.settings.json
```

## 5) Run the Timer Job Locally

```bash
func start
```

Watch logs for trigger execution entries and your service output.

If schedule is infrequent, you can temporarily reduce interval for testing,
then restore production cadence.

## 6) Add a Second Scheduled Function

Add another timer function module:

```bash
afs add timer cleanup_cache --project-root .
```

Preview first if preferred:

```bash
afs add timer cleanup_cache --project-root . --dry-run
```

After adding, verify:

- `app/functions/cleanup_cache.py` exists
- `function_app.py` includes import and registration
- `tests/test_cleanup_cache.py` exists (if tests are enabled)

## 7) Example Custom Job Logic

Keep trigger module minimal and route to service code:

```python
from __future__ import annotations

import logging

import azure.functions as func

from app.services.maintenance_service import prune_old_records

cleanup_cache_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@cleanup_cache_blueprint.timer_trigger(
    arg_name="timer",
    schedule="0 0 * * * *",
    run_on_startup=False,
    use_monitor=True,
)
def cleanup_cache(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("cleanup_cache is running late")
    removed = prune_old_records()
    logging.info("cleanup_cache removed %s records", removed)
```

## 8) Testing Strategy

Generated timer tests use lightweight stubs (`SimpleNamespace`) to invoke the
function directly.

Typical workflow:

```bash
pytest
```

For robust jobs, add tests around service functions in `app/services/` and keep
trigger tests focused on wiring.

## Troubleshooting Notes

!!! warning "No timer executions appear"
    Check that Azurite is running and `local.settings.json` exists with
    `AzureWebJobsStorage` configured.

!!! warning "Past due warnings repeatedly"
    Reduce local machine load, use less frequent schedules, and avoid long work
    directly inside trigger handlers.

## Next Steps

- See [Templates](../guide/templates.md) for queue/blob/service bus options.
- See [Expanding Your Project](../guide/expanding.md) for add-command flows.
- See [Troubleshooting](../guide/troubleshooting.md) for runtime diagnostics.
