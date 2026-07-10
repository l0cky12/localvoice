from __future__ import annotations

import subprocess
from collections.abc import Callable

_TEXT_MIME = "text/plain;charset=utf-8"


def copy_text(
    text: str,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> None:
    if not text:
        raise ValueError("Refusing to copy empty text")
    runner(
        ["wl-copy", "--type", _TEXT_MIME],
        input=text.encode("utf-8"),
        check=True,
        timeout=5,
        shell=False,
    )


def save_clipboard(
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> bytes | None:
    """Best-effort snapshot of the current text clipboard.

    Returns the raw bytes of the ``text/plain`` selection, or ``None`` when the
    clipboard is empty, holds only non-text content, or cannot be read (for
    example when ``wl-paste`` is missing). Only text is preserved; images and
    other MIME types are intentionally not snapshotted — see the README.
    """
    try:
        result = runner(
            ["wl-paste", "--no-newline", "--type", "text/plain"],
            capture_output=True,
            timeout=5,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    return result.stdout


def restore_clipboard(
    data: bytes,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> None:
    """Best-effort restore of a previously saved text clipboard snapshot."""
    if not data:
        return
    try:
        runner(
            ["wl-copy", "--type", _TEXT_MIME],
            input=data,
            check=True,
            timeout=5,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return
