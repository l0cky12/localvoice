from __future__ import annotations

import collections
import subprocess
import tempfile
import threading
import wave
from collections.abc import Callable
from pathlib import Path


class ContinuousListener:
    """PipeWire PCM listener segmented by local WebRTC VAD."""

    def __init__(self, on_utterance: Callable[[Path], None], target: str | None = None) -> None:
        self.on_utterance = on_utterance
        self.target = target
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def active(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.active:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="localvoice-vad")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._process and self._process.poll() is None:
            self._process.terminate()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        import webrtcvad  # type: ignore[import-untyped]

        args = ["pw-record", "--format", "s16", "--rate", "16000", "--channels", "1", "-"]
        if self.target:
            args[1:1] = ["--target", self.target]
        self._process = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        assert self._process.stdout is not None
        vad = webrtcvad.Vad(2)
        frame_bytes = 960  # 30 ms, 16 kHz, 16-bit mono
        pre_roll: collections.deque[bytes] = collections.deque(maxlen=10)
        speech: list[bytes] = []
        silence = 0
        while not self._stop.is_set():
            frame = self._process.stdout.read(frame_bytes)
            if len(frame) != frame_bytes:
                break
            voiced = vad.is_speech(frame, 16000)
            if voiced:
                if not speech:
                    speech.extend(pre_roll)
                speech.append(frame)
                silence = 0
            elif speech:
                speech.append(frame)
                silence += 1
                if silence >= 20:
                    if len(speech) >= 15:
                        self._emit(speech)
                    speech, silence = [], 0
            else:
                pre_roll.append(frame)
        if len(speech) >= 15:
            self._emit(speech)

    def _emit(self, frames: list[bytes]) -> None:
        directory = Path(tempfile.mkdtemp(prefix="localvoice-"))
        path = directory / "utterance.wav"
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(b"".join(frames))
        self.on_utterance(path)
