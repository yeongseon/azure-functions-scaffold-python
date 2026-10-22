import json
from pathlib import Path

import azure.functions as func
from test_generated_webhook_signature import _CONTEXT, _imported

from azure_functions_scaffold.scaffolder import scaffold_project


def test_anonymous_health_exposes_only_liveness(tmp_path: Path) -> None:
    root = scaffold_project("health-boundary", tmp_path)
    with _imported(root, "app.functions.health") as module:
        response = module.health(
            func.HttpRequest("GET", "http://localhost/api/health", body=b""), _CONTEXT
        )
    assert json.loads(response.get_body()) == {"status": "ok"}
