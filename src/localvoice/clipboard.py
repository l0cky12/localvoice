from __future__ import annotations

import subprocess
from collections.abc import Callable


def copy_text(
    text: str,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> None:
    if not text:
        raise ValueError("Refusing to copy empty text")
    runner(
        ["wl-copy", "--type", "text/plain;charset=utf-8"],
        input=text.encode("utf-8"),
        check=True,
        timeout=5,
        shell=False,
    )
