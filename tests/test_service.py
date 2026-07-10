from __future__ import annotations

from pathlib import Path

from localvoice.config import Settings
from localvoice.hyprland import WindowTarget
from localvoice.service import DictationService


def test_recording_start_stop_modes(monkeypatch, tmp_path: Path) -> None:
    service = DictationService(Settings())
    calls: list[str] = []
    monkeypatch.setattr(service.hyprland, "require_session", lambda: None)
    monkeypatch.setattr(service.hyprland, "capture_target", lambda: WindowTarget("0x1", "kitty"))
    monkeypatch.setattr(
        service.recorder, "start", lambda path, target: calls.append(f"start:{target}")
    )
    monkeypatch.setattr(type(service.recorder), "active", property(lambda _self: False))
    service.start()
    assert service.target == WindowTarget("0x1", "kitty")
    assert calls == ["start:None"]


def test_success_keeps_gui_and_clipboard_fallback(monkeypatch, tmp_path: Path) -> None:
    texts: list[str] = []
    statuses: list[str] = []
    copied: list[str] = []
    service = DictationService(Settings(), texts.append, statuses.append)
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(service.transcriber, "transcribe", lambda _path: "private text")
    monkeypatch.setattr("localvoice.service.copy_text", copied.append)
    monkeypatch.setattr("localvoice.service.save_clipboard", lambda: None)
    monkeypatch.setattr(service.hyprland, "restore_and_paste", lambda *_args: False)
    service._finish(audio, WindowTarget("0x1", "kitty"))
    assert copied == ["private text"]
    assert texts == ["private text"]
    assert statuses[-1] == "Copied; automatic paste unavailable"


def test_successful_paste_restores_previous_clipboard(monkeypatch, tmp_path: Path) -> None:
    statuses: list[str] = []
    restored: list[bytes] = []
    service = DictationService(Settings(), on_status=statuses.append)
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(service.transcriber, "transcribe", lambda _path: "dictated text")
    monkeypatch.setattr("localvoice.service.copy_text", lambda _text: None)
    monkeypatch.setattr("localvoice.service.save_clipboard", lambda: b"earlier user clipboard")
    monkeypatch.setattr("localvoice.service.restore_clipboard", restored.append)
    monkeypatch.setattr("localvoice.service.sleep", lambda _seconds: None)
    monkeypatch.setattr(service.hyprland, "restore_and_paste", lambda *_args: True)
    service._finish(audio, WindowTarget("0x1", "kitty"))
    assert restored == [b"earlier user clipboard"]
    assert statuses[-1] == "Pasted"


def test_failed_paste_leaves_transcription_on_clipboard(monkeypatch, tmp_path: Path) -> None:
    restored: list[bytes] = []
    service = DictationService(Settings())
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(service.transcriber, "transcribe", lambda _path: "dictated text")
    monkeypatch.setattr("localvoice.service.copy_text", lambda _text: None)
    monkeypatch.setattr("localvoice.service.save_clipboard", lambda: b"earlier user clipboard")
    monkeypatch.setattr("localvoice.service.restore_clipboard", restored.append)
    monkeypatch.setattr(service.hyprland, "restore_and_paste", lambda *_args: False)
    service._finish(audio, WindowTarget("0x1", "kitty"))
    assert restored == []  # transcription stays on the clipboard as the fallback
