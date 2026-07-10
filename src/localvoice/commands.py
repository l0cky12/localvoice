from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


class CommandError(RuntimeError):
    pass


def run_command(args: Sequence[str], *, timeout: float = 5) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(  # noqa: S603 - fixed argv, shell explicitly disabled
            list(args), check=True, capture_output=True, timeout=timeout, shell=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CommandError(f"Command failed: {args[0]}") from exc


def run_json(args: Sequence[str], *, timeout: float = 5) -> Any:
    completed = run_command(args, timeout=timeout)
    try:
        return json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CommandError(f"Invalid JSON from {args[0]}") from exc


@dataclass(frozen=True, slots=True)
class CommandStatus:
    available: bool
    detail: str
