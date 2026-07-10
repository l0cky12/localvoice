from __future__ import annotations

import re
import signal
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PipeWireDevice:
    identifier: str
    name: str
    kind: str


def parse_wpctl_status(text: str) -> list[PipeWireDevice]:
    devices: list[PipeWireDevice] = []
    section: str | None = None
    for raw in text.splitlines():
        line = raw.strip().replace("│", "").replace("├", "").replace("└", "")
        if "Sources:" in line:
            section = "input"
            continue
        if "Sinks:" in line:
            section = "output"
            continue
        if line.endswith(":") and not line.startswith(("Sources:", "Sinks:")):
            section = None
        if section:
            match = re.search(r"(?:\*\s*)?(\d+)\.\s+(.+?)(?:\s+\[vol:.*)?$", line)
            if match:
                devices.append(PipeWireDevice(match.group(1), match.group(2).strip(), section))
    return devices


def list_devices(
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[PipeWireDevice]:
    result = runner(
        ["wpctl", "status", "--name"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
        shell=False,
    )
    return parse_wpctl_status(result.stdout)


class PipeWireRecorder:
    def __init__(self, popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen) -> None:
        self._popen = popen
        self._process: subprocess.Popen[bytes] | None = None
        self.path: Path | None = None

    @property
    def active(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, path: Path, target: str | None = None) -> None:
        if self.active:
            raise RuntimeError("Recording is already active")
        args = ["pw-record", "--format", "s16", "--rate", "16000", "--channels", "1"]
        if target:
            args.extend(["--target", target])
        args.append(str(path))
        self.path = path
        self._process = self._popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, shell=False
        )

    def stop(self, timeout: float = 5) -> Path:
        if not self._process or not self.path:
            raise RuntimeError("Recording is not active")
        process, path = self._process, self.path
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        self._process = None
        self.path = None
        if not path.is_file() or path.stat().st_size <= 44:
            raise RuntimeError("PipeWire produced no microphone audio")
        return path


def inputs(devices: Iterable[PipeWireDevice]) -> list[PipeWireDevice]:
    return [device for device in devices if device.kind == "input"]


def outputs(devices: Iterable[PipeWireDevice]) -> list[PipeWireDevice]:
    return [device for device in devices if device.kind == "output"]
