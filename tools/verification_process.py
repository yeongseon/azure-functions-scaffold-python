from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from types import FrameType

from tools.verification_evidence import redact


def _signal_group(pid: int, number: signal.Signals) -> None:
    try:
        os.killpg(pid, number)
    except ProcessLookupError:
        return


def _group_alive(pid: int) -> bool:
    for stat in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = stat.read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == pid and fields[0] != "Z":
                return True
        except (OSError, IndexError, ValueError):
            continue
    return False


def terminate(process: subprocess.Popen[str], registry: Path | None = None) -> None:
    owned = {process.pid}
    if registry is not None:
        owned.update(int(pid) for pid in registry.read_text().splitlines())
    for pid in owned:
        _signal_group(pid, signal.SIGTERM)
    deadline = time.monotonic() + 5
    while any(_group_alive(pid) for pid in owned) and time.monotonic() < deadline:
        process.poll()
        time.sleep(0.05)
    for pid in owned:
        if _group_alive(pid):
            _signal_group(pid, signal.SIGKILL)
    process.wait()


@contextmanager
def configured(values: Mapping[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def child(
    command: list[str], log: Path, cwd: Path | None = None
) -> Iterator[subprocess.Popen[str]]:
    log.parent.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryFile(mode="w+", encoding="utf-8") as output,
        tempfile.TemporaryDirectory(prefix="verification-owned-") as temporary,
    ):
        registry = Path(
            os.environ.get("VERIFICATION_OWNED_REGISTRY", str(Path(temporary) / "sessions"))
        )
        registry.touch(exist_ok=True)
        with subprocess.Popen(
            command,
            cwd=cwd,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
            env={**os.environ, "VERIFICATION_OWNED_REGISTRY": str(registry)},
        ) as process:
            with registry.open("a") as stream:
                stream.write(f"{process.pid}\n")

            def interrupted(number: int, frame: FrameType | None) -> None:
                raise KeyboardInterrupt(number)

            previous = {
                sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)
            }
            try:
                yield process
            finally:
                for sig in previous:
                    signal.signal(sig, signal.SIG_IGN)
                terminate(
                    process, registry if "VERIFICATION_OWNED_REGISTRY" not in os.environ else None
                )
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
                output.seek(0)
                text = redact(output.read())
                log.write_text(text, encoding="utf-8")
                print(text, end="")


def run(command: list[str], log: Path, timeout: float = 600, *, cwd: Path | None = None) -> int:
    try:
        with child(command, log, cwd) as process:
            try:
                code = process.wait(timeout=timeout)
                return code if code >= 0 else 128 - code
            except subprocess.TimeoutExpired:
                return 124
    except FileNotFoundError as error:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(redact(str(error)))
        return 127
