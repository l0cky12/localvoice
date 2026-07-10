from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .commands import CommandError, run_command, run_json

_ADDRESS = re.compile(r"^(?:0x)?[0-9a-fA-F]+$")


@dataclass(frozen=True, slots=True)
class WindowTarget:
    address: str
    window_class: str


def is_hyprland_wayland(env: Mapping[str, str] | None = None) -> bool:
    current = os.environ if env is None else env
    return bool(
        current.get("XDG_SESSION_TYPE") == "wayland"
        and current.get("HYPRLAND_INSTANCE_SIGNATURE")
        and current.get("WAYLAND_DISPLAY")
    )


def parse_window(data: Any) -> WindowTarget | None:
    if not isinstance(data, dict):
        return None
    raw_address = data.get("address")
    if not isinstance(raw_address, str) or not _ADDRESS.fullmatch(raw_address):
        return None
    window_class = data.get("class")
    return WindowTarget(raw_address, window_class if isinstance(window_class, str) else "")


def parse_clients(data: Any) -> set[str]:
    if not isinstance(data, list):
        raise ValueError("Hyprland clients JSON must be a list")
    addresses: set[str] = set()
    for item in data:
        target = parse_window(item)
        if target:
            addresses.add(target.address)
    return addresses


class HyprlandController:
    def __init__(
        self,
        json_runner: Callable[[Sequence[str]], Any] = run_json,
        command_runner: Callable[[Sequence[str]], object] = run_command,
    ) -> None:
        self._json = json_runner
        self._command = command_runner

    def require_session(self) -> None:
        if not is_hyprland_wayland():
            raise CommandError("LocalVoice requires Hyprland running on Wayland")

    def active_window(self) -> WindowTarget | None:
        return parse_window(self._json(["hyprctl", "activewindow", "-j"]))

    def capture_target(self) -> WindowTarget | None:
        target = self.active_window()
        if target and target.window_class.lower() not in {"localvoice", "localvoice.localvoice"}:
            return target
        return None

    def window_exists(self, address: str) -> bool:
        return address in parse_clients(self._json(["hyprctl", "clients", "-j"]))

    def restore_and_paste(self, target: WindowTarget, modifiers: str, key: str) -> bool:
        if not self.window_exists(target.address):
            return False
        self._command(["hyprctl", "dispatch", "focuswindow", f"address:{target.address}"])
        # The transcription itself is never placed in an argument.
        self._command(
            ["hyprctl", "dispatch", "sendshortcut", modifiers, key, f"address:{target.address}"]
        )
        return True
