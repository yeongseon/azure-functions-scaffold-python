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


def main() -> int:
    full_required = sys.argv[1] == "true"
    docs_changed = sys.argv[2] == "true"
    results: dict[str, JobResult] = json.load(sys.stdin)
    for job, data in sorted(results.items()):
        print(f"{job}: {data['result']}")

    expected = dict.fromkeys(MATRIX_JOBS, "success" if full_required else "skipped")
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
