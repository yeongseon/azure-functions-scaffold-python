from __future__ import annotations

import json
import sys
from typing import TypedDict


class JobResult(TypedDict):
    result: str


MATRIX_JOBS = (
    "quality",
    "test",
    "minimum-dependencies",
    "artifact-build",
    "artifact-python310-negative",
    "artifact-python311",
    "generated-host-smoke",
)


def parse_boolean(value: str, name: str) -> bool:
    match value:
        case "true":
            return True
        case "false":
            return False
        case _:
            print(f"::error::{name} must be exactly 'true' or 'false'", file=sys.stderr)
            raise SystemExit(1)


def main() -> int:
    full_required = parse_boolean(sys.argv[1], "full_required")
    docs_changed = parse_boolean(sys.argv[2], "docs_changed")
    results: dict[str, JobResult] = json.load(sys.stdin)
    for job, data in sorted(results.items()):
        print(f"{job}: {data['result']}")

    if not full_required and not docs_changed:
        print("::error::Classifier disabled both full CI and docs CI", file=sys.stderr)
        return 1

    expected = dict.fromkeys(results, "success")
    expected.update(dict.fromkeys(MATRIX_JOBS, "success" if full_required else "skipped"))
    expected["changes"] = "success"
    expected["docs-check"] = "success" if docs_changed else "skipped"
    failed = sorted(job for job, wanted in expected.items() if results[job]["result"] != wanted)
    if failed:
        print(f"::error::Required checks had unexpected results: {failed}", file=sys.stderr)
        return 1
    print("All gating jobs produced their expected results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
