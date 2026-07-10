from __future__ import annotations

import subprocess
from typing import Any

from localvoice.clipboard import copy_text, restore_clipboard, save_clipboard


def test_wl_copy_receives_text_only_via_stdin() -> None:
    captured: dict[str, Any] = {}

    def runner(args: list[str], **kwargs: Any) -> None:
        captured["args"], captured["kwargs"] = args, kwargs

    payload_text = "hello; $(never-a-shell)"
    copy_text(payload_text, runner=runner)  # type: ignore[arg-type]
    assert payload_text not in captured["args"]
    assert captured["args"] == ["wl-copy", "--type", "text/plain;charset=utf-8"]
    assert captured["kwargs"]["input"] == payload_text.encode()
    assert captured["kwargs"]["shell"] is False


def test_save_clipboard_returns_bytes_and_handles_empty() -> None:
    def full(_args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess([], 0, stdout=b"prior text", stderr=b"")

    def empty(_args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"Nothing is copied")

    assert save_clipboard(runner=full) == b"prior text"  # type: ignore[arg-type]
    assert save_clipboard(runner=empty) is None  # type: ignore[arg-type]


def test_save_clipboard_swallows_missing_tool() -> None:
    def missing(_args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("wl-paste")

    assert save_clipboard(runner=missing) is None  # type: ignore[arg-type]


def test_restore_clipboard_writes_saved_bytes() -> None:
    captured: dict[str, Any] = {}

    def runner(args: list[str], **kwargs: Any) -> None:
        captured["args"], captured["input"] = args, kwargs["input"]

    restore_clipboard(b"prior text", runner=runner)  # type: ignore[arg-type]
    assert captured["args"] == ["wl-copy", "--type", "text/plain;charset=utf-8"]
    assert captured["input"] == b"prior text"
