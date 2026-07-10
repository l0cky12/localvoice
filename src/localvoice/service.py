from __future__ import annotations

import shutil
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from .clipboard import copy_text
from .config import Settings
from .hyprland import HyprlandController, WindowTarget
from .pipewire import PipeWireRecorder
from .transcriber import LocalTranscriber
from .vad import ContinuousListener


class DictationService:
    def __init__(
        self,
        settings: Settings,
        on_text: Callable[[str], None] = lambda _text: None,
        on_status: Callable[[str], None] = lambda _status: None,
    ) -> None:
        self.settings = settings
        self.on_text, self.on_status = on_text, on_status
        self.hyprland = HyprlandController()
        self.recorder = PipeWireRecorder()
        self.transcriber = LocalTranscriber(
            settings.model, settings.compute_type, settings.language
        )
        self.target: WindowTarget | None = None
        self.continuous: ContinuousListener | None = None
        self._directory: Path | None = None

    def start(self, target_address: str | None = None) -> None:
        self.hyprland.require_session()
        if self.recorder.active:
            return
        active = self.hyprland.capture_target()
        self.target = WindowTarget(target_address, "") if target_address else active
        self._directory = Path(tempfile.mkdtemp(prefix="localvoice-"))
        self.recorder.start(self._directory / "recording.wav", self.settings.input_device)
        self.on_status("Recording")

    def stop(self) -> None:
        if not self.recorder.active:
            return
        try:
            audio = self.recorder.stop()
        except Exception:
            self._cleanup()
            raise
        self.on_status("Transcribing locally")
        threading.Thread(target=self._finish, args=(audio, self.target), daemon=True).start()

    def toggle(self, target_address: str | None = None) -> None:
        self.stop() if self.recorder.active else self.start(target_address)

    def continuous_start(self) -> None:
        self.hyprland.require_session()
        if self.continuous and self.continuous.active:
            return
        self.target = self.hyprland.capture_target()
        self.continuous = ContinuousListener(self._continuous_utterance, self.settings.input_device)
        self.continuous.start()
        self.on_status("Continuous listening")

    def continuous_stop(self) -> None:
        if self.continuous:
            self.continuous.stop()
            self.continuous = None
        self.on_status("Idle")

    def _continuous_utterance(self, audio: Path) -> None:
        self._finish(audio, self.hyprland.capture_target() or self.target)

    def _finish(self, audio: Path, target: WindowTarget | None) -> None:
        try:
            text = self.transcriber.transcribe(audio)
            if not text:
                self.on_status("No speech detected")
                return
            copy_text(text)
            self.on_text(text)
            pasted = False
            if target:
                try:
                    pasted = self.hyprland.restore_and_paste(
                        target, self.settings.paste_modifiers, self.settings.paste_key
                    )
                except Exception:
                    pasted = False
            self.on_status("Pasted" if pasted else "Copied; automatic paste unavailable")
        except Exception as exc:
            self.on_status(f"Error: {exc}")
        finally:
            try:
                parent = audio.parent
                audio.unlink(missing_ok=True)
                if parent.name.startswith("localvoice-"):
                    shutil.rmtree(parent, ignore_errors=True)
            finally:
                self._directory = None

    def _cleanup(self) -> None:
        if self._directory:
            shutil.rmtree(self._directory, ignore_errors=True)
            self._directory = None
