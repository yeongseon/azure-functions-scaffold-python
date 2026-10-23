from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Literal
import xml.etree.ElementTree as ET

Status = Literal["PASS", "FAIL", "INCOMPLETE", "NOT_APPLICABLE"]


def read_xml_root(path: Path) -> ET.Element:
    """Parse a locally generated report, refusing entity declarations."""
    data = path.read_bytes()
    if b"<!ENTITY" in data.upper():
        raise ValueError("XML reports must not declare entities")
    return ET.fromstring(data)


@dataclass(frozen=True, slots=True)
class Summary:
    schema_version: int
    lane: str
    command: tuple[str, ...]
    selected: int
    passed: int
    failed: int
    skipped: int
    status: Status
    exit_code: int
    required: bool = True
    scope: str = "PARTIAL"
    reason: str = ""
    supporting_files: tuple[str, ...] = ()
    candidate_version: str = ""
    artifact_sha256: str = ""
    generated_python: str = ""
    sdk_version: str = ""
    generated_digest: str = ""
    deployed_artifact_identity: Status = "NOT_APPLICABLE"
    diagnostics_status: str = "NOT_APPLICABLE"


_REDACTED = "[REDACTED]"
_QUOTED = r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'"
_AUTHORIZATION = re.compile(
    r"(?im)(?P<key>(?:proxy-)?authorization[\"']?\s*[:=]\s*)(?P<value>" + _QUOTED + r"|[^\r\n\"<]+)"
)
_URL_CREDENTIALS = re.compile(r"(https?://)[^/@\s\"']+:[^/@\s\"']+@")
_SECRET_FIELD = re.compile(
    r"(?i)(?<![\w-])(?P<key>(?:[\w.-]*(?:token|password|passwd|secret|api[_-]?key|"
    r"connection[_-]?string)|AccountKey|SharedAccessKey|SharedAccessSignature|"
    r"AzureWebJobsStorage|InstrumentationKey|x-functions-key|code|sig|sas)"
    r"[\"']?\s*[:=]\s*)(?P<value>" + _QUOTED + r"|[^\s;&<>\"',]+)"
)
_SECRET_ENV_NAME = re.compile(r"(?i)secret|token|password|connection|key|sas")
_TEXT_SUFFIXES = frozenset({".log", ".txt", ".xml", ".json", ".md"})


def _mask(match: re.Match[str]) -> str:
    value = match.group("value")
    quote = value[0] if value[:1] in {'"', "'"} else ""
    return f"{match.group('key')}{quote}{_REDACTED}{quote}"


def _known_secrets() -> list[str]:
    values = {
        value
        for key, value in os.environ.items()
        if len(value) >= 6 and _SECRET_ENV_NAME.search(key)
    }
    return sorted(values | {json.dumps(value)[1:-1] for value in values}, key=len, reverse=True)


def redact(text: str) -> str:
    for value in _known_secrets():
        text = text.replace(value, _REDACTED)
    text = _AUTHORIZATION.sub(_mask, text)
    text = _URL_CREDENTIALS.sub(r"\1" + _REDACTED + "@", text)
    return _SECRET_FIELD.sub(_mask, text)


def redact_json(value: object) -> object:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, (list, tuple)):
        return [redact_json(item) for item in value]
    if isinstance(value, dict):
        return {redact(str(key)): redact_json(item) for key, item in value.items()}
    return value


def dump_json(value: object) -> str:
    return json.dumps(redact_json(value), indent=2) + "\n"


def _redact_file_text(suffix: str, text: str) -> str:
    if suffix == ".json":
        try:
            return dump_json(json.loads(text))
        except ValueError:
            return redact(text)
    return redact(text)


def environment() -> dict[str, str]:
    metadata = {"python": platform.python_version(), "platform": platform.platform()}
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    metadata["source_commit"] = result.stdout.strip()
    for package in ("azure-functions-scaffold", "azure-functions", "azure-functions-doctor"):
        try:
            metadata[package] = version(package)
        except PackageNotFoundError:
            metadata[package] = "not installed"
    return metadata


def collect(directory: Path, command: list[str], exit_code: int) -> Summary:
    cases: list[ET.Element] = []
    for path in directory.rglob("*junit*.xml"):
        root = read_xml_root(path)
        suites = list(root.iter("testsuite"))
        if not suites:
            raise ValueError("JUnit contains no testsuite")
        for suite in suites:
            actual_cases = list(suite.iter("testcase"))
            for counter, outcome in (
                ("tests", None),
                ("failures", "failure"),
                ("errors", "error"),
                ("skipped", "skipped"),
            ):
                actual = (
                    len(actual_cases)
                    if outcome is None
                    else sum(case.find(outcome) is not None for case in actual_cases)
                )
                if counter in suite.attrib and int(suite.attrib[counter]) != actual:
                    raise ValueError(f"JUnit counter mismatch: {counter}")
        cases.extend(root.iter("testcase"))
    failed = sum(c.find("failure") is not None or c.find("error") is not None for c in cases)
    skipped = sum(c.find("skipped") is not None for c in cases)
    passed = len(cases) - failed - skipped
    unexpected_skips = skipped
    if directory.name == "test":
        unexpected_skips -= sum(
            (skip := case.find("skipped")) is not None
            and skip.get("message", "").startswith("intentional historical content: ")
            and "test_docs_cli_examples" in case.get("classname", "")
            for case in cases
        )
    status: Status = "PASS"
    if exit_code or failed:
        status = "FAIL"
    elif not passed or unexpected_skips:
        status = "INCOMPLETE"
    return Summary(
        1,
        directory.name,
        tuple(command),
        len(cases),
        passed,
        failed,
        skipped,
        status,
        exit_code or int(status != "PASS"),
        reason="Required positive execution with no unexpected skips" if status != "PASS" else "",
    )


def publish(summary: Summary) -> None:
    text = redact(
        f"{summary.lane}: {summary.status} | scope={summary.scope} selected={summary.selected} "
        f"passed={summary.passed} failed={summary.failed} skipped={summary.skipped} "
        f"exit={summary.exit_code} | {summary.reason}"
    )
    print(text)
    if destination := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(destination).open("a", encoding="utf-8") as stream:
            stream.write("\n- " + text + "\n")


def save(directory: Path, summary: Summary) -> Summary:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.suffix not in _TEXT_SUFFIXES:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        redacted = _redact_file_text(path.suffix, original)
        if redacted != original:
            path.write_text(redacted, encoding="utf-8")
    (directory / "environment.json").write_text(dump_json(environment()))
    summary = replace(
        summary,
        command=tuple(redact(p) for p in summary.command),
        reason=redact(summary.reason),
        supporting_files=tuple(
            str(p) for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "summary.json"
        ),
    )
    serialized = dump_json(asdict(summary))
    (directory / "summary.json").write_text(serialized)
    return Summary(**json.loads(serialized))


def report(root: Path) -> int:
    paths = sorted(root.rglob("summary.json"))
    for path in paths:
        publish(Summary(**json.loads(path.read_text())))
    if not paths:
        print("No saved verification results")
    return int(not paths)
