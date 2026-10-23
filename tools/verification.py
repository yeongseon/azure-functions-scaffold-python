from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from tools.verification_azure import azure
from tools.verification_environment import clean, doctor
from tools.verification_evidence import Status, Summary, collect, publish, report, save
from tools.verification_generated import (
    LaneFailure,
    candidate,
    existing_project,
    generate,
    generated,
)
from tools.verification_host import MissingPrerequisite, host_smoke
from tools.verification_manifest import TEMPLATES
from tools.verification_process import configured, run


def fresh(directory: Path) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    (directory / "logs").mkdir(parents=True)


def aggregate(lane: str, outcomes: list[Summary]) -> int:
    status: Status = "PASS"
    if any(item.status == "FAIL" for item in outcomes):
        status = "FAIL"
    elif not outcomes or any(item.status != "PASS" for item in outcomes):
        status = "INCOMPLETE"
    directory = Path("test-results") / lane
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "lanes.json").write_text(json.dumps([asdict(s) for s in outcomes], indent=2))
    summary = Summary(
        1,
        lane,
        ("make", lane),
        sum(s.selected for s in outcomes),
        sum(s.passed for s in outcomes),
        sum(s.failed for s in outcomes),
        sum(s.skipped for s in outcomes),
        status,
        int(status != "PASS"),
        scope="FULL_LOCAL" if lane == "verify" else "PARTIAL",
        reason="; ".join(f"{s.lane}={s.status}" for s in outcomes),
    )
    publish(save(directory, summary))
    return summary.exit_code


def execute(lane: str, extra: list[str]) -> int:
    directory = Path("test-results") / lane
    fresh(directory)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/e2e",
        "--cov-report=xml:" + str(directory / "coverage.xml"),
        *extra,
        "--junitxml=" + str(directory / "junit.xml"),
    ]
    try:
        if lane == "existing-project":
            summary = existing_project(Path(extra[0]).resolve(), directory.resolve())
            publish(save(directory, summary))
            return summary.exit_code
        if lane == "azure-e2e":
            outcomes = azure(directory)
            if len(outcomes) == 1 and outcomes[0].status == "INCOMPLETE":
                summary = outcomes[0]
                publish(save(directory, summary))
                return summary.exit_code
            return aggregate(lane, outcomes)
        if lane == "generated-project":
            selected = tuple(extra) if extra else TEMPLATES
            if any(name not in TEMPLATES for name in selected):
                raise LaneFailure("Unknown template selection")
            return aggregate(lane, generated(directory.resolve(), selected))
        if lane in {"integration", "host-smoke", "wheel-smoke"}:
            outcomes = []
            with candidate(directory.resolve()) as artifact:
                if lane == "integration":
                    with configured({"VERIFICATION_WHEEL": str(artifact.wheel)}):
                        outcomes.extend(generated(directory.resolve() / "generated-project"))
                if lane != "wheel-smoke":
                    summary = host_smoke(artifact, directory.resolve() / "host-smoke")
                    publish(save(directory / "host-smoke", summary))
                    outcomes.append(summary)
                else:
                    with tempfile.TemporaryDirectory(prefix="scaffold-wheel-smoke-") as temporary:
                        generate(artifact, Path(temporary), "http")
                    outcomes.append(
                        Summary(
                            1,
                            lane,
                            ("installed-cli", "generate"),
                            1,
                            1,
                            0,
                            0,
                            "PASS",
                            0,
                            candidate_version=artifact.version,
                            artifact_sha256=artifact.digest,
                        )
                    )
            return aggregate(lane, outcomes)
        code = run(command, directory / "logs/pytest.log", 1200)
        summary = collect(directory, command, code)
    except MissingPrerequisite as error:
        summary = Summary(1, lane, tuple(command), 0, 0, 0, 0, "INCOMPLETE", 2, reason=str(error))
    except (OSError, ValueError, LaneFailure, ET.ParseError) as error:
        summary = Summary(1, lane, tuple(command), 0, 0, 0, 0, "FAIL", 1, reason=str(error))
    except KeyboardInterrupt:
        summary = Summary(
            1,
            lane,
            tuple(command),
            0,
            0,
            0,
            0,
            "INCOMPLETE",
            130,
            reason="Interrupted; owned children terminated",
        )
    publish(save(directory, summary))
    return summary.exit_code


def targets() -> int:
    directory = Path("test-results/verify")
    fresh(directory)
    outcomes = []
    for target in ("check", "test", "integration", "wheel-smoke", "build", "docs"):
        path = Path("test-results") / target / "summary.json"
        path.unlink(missing_ok=True)
        code = run(["make", target], directory / f"logs/{target}.log", 3600)
        if path.exists():
            summary = Summary(**json.loads(path.read_text()))
            if code and summary.status == "PASS":
                summary = replace(summary, status="FAIL", exit_code=code)
        else:
            quality = target == "check"
            summary = Summary(
                1,
                target,
                ("make", target),
                int(quality),
                int(quality and not code),
                int(bool(code)),
                0,
                ("FAIL" if code else "PASS") if quality else "INCOMPLETE",
                code or int(not quality),
                reason="Required lane summary missing",
            )
        outcomes.append(summary)
    return aggregate("verify", outcomes)


def focused(lane: str, command: list[str]) -> int:
    directory = Path("test-results") / lane
    fresh(directory)
    code = run(command, directory / "logs/runner.log", 1200)
    summary = Summary(
        1,
        lane,
        tuple(command),
        1,
        int(code == 0),
        int(code != 0),
        0,
        "FAIL" if code else "PASS",
        code,
    )
    publish(save(directory, summary))
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lane",
        choices=(
            "test",
            "integration",
            "generated-project",
            "existing-project",
            "host-smoke",
            "wheel-smoke",
            "azure-e2e",
            "verify",
            "doctor",
            "clean",
            "report",
            "focused",
            "quality",
            "record",
        ),
    )
    args, extra = parser.parse_known_args()
    match args.lane:
        case "quality":
            return focused("check", ["make", "check-steps"])
        case "doctor":
            return doctor()
        case "clean":
            clean(Path.cwd())
            return 0
        case "report":
            return report(Path("test-results"))
        case "verify":
            return targets()
        case "focused":
            return focused(extra[0], [sys.executable, *extra[1:]])
        case "record":
            directory = Path("test-results") / extra[0]
            summary = collect(directory, ["pytest"], int(extra[1]))
            publish(save(directory, summary))
            return summary.exit_code
        case _:
            return execute(args.lane, extra)


if __name__ == "__main__":
    raise SystemExit(main())
