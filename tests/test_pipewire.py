from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from localvoice.pipewire import PipeWireRecorder, inputs, outputs, parse_wpctl_status

STATUS = """Audio
 ├─ Sinks:
 │  * 42. Built-in Audio Stereo [vol: 0.50]
 ├─ Sources:
 │  * 51. USB Microphone Mono [vol: 1.00]
Video
"""


def test_pipewire_device_handling() -> None:
    devices = parse_wpctl_status(STATUS)
    assert [(d.identifier, d.name) for d in inputs(devices)] == [("51", "USB Microphone Mono")]
    assert [(d.identifier, d.name) for d in outputs(devices)] == [("42", "Built-in Audio Stereo")]


class FakeProcess:
    def __init__(self) -> None:
        self.running = True

    def poll(self) -> int | None:
        return None if self.running else 0

    def send_signal(self, _signal: int) -> None:
        self.running = False

    def wait(self, timeout: float) -> int:
        return 0

    def kill(self) -> None:
        self.running = False


def test_recorder_modes_use_pipewire_and_selected_target(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []
    process = FakeProcess()

    def popen(args: list[str], **kwargs: Any) -> FakeProcess:
        calls.append((args, kwargs))
        return process

    recorder = PipeWireRecorder(popen=popen)  # type: ignore[arg-type]
    audio = tmp_path / "capture.wav"
    recorder.start(audio, "51")
    audio.write_bytes(b"R" * 128)
    assert recorder.active
    assert calls[0][0][:2] == ["pw-record", "--format"]
    assert calls[0][0][calls[0][0].index("--target") : calls[0][0].index("--target") + 2] == [
        "--target",
        "51",
    ]
    assert recorder.stop() == audio


def test_recorder_rejects_empty_audio(tmp_path: Path) -> None:
    process = FakeProcess()
    recorder = PipeWireRecorder(popen=lambda *_args, **_kwargs: process)  # type: ignore[arg-type]
    audio = tmp_path / "empty.wav"
    recorder.start(audio)
    audio.write_bytes(b"")
    with pytest.raises(RuntimeError, match="no microphone audio"):
        recorder.stop()
