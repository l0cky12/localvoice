from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

from .config import Settings
from .hyprland import is_hyprland_wayland
from .pipewire import inputs, list_devices


def report(settings: Settings | None = None) -> tuple[bool, list[str]]:
    active = settings or Settings.load()
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Hyprland Wayland", is_hyprland_wayland(), "session variables"))
    for command in ("hyprctl", "pw-record", "wpctl", "wl-copy"):
        checks.append((command, shutil.which(command) is not None, "executable"))
    for module in ("PySide6", "faster_whisper", "webrtcvad"):
        checks.append((module, importlib.util.find_spec(module) is not None, "Python dependency"))
    try:
        microphones = inputs(list_devices())
        checks.append(("Microphone", bool(microphones), f"{len(microphones)} PipeWire source(s)"))
    except (OSError, subprocess.SubprocessError):
        checks.append(("Microphone", False, "PipeWire query failed"))
    model_path = Path(active.model).expanduser()
    model_local = model_path.is_dir()
    cache = Path(os.getenv("HF_HOME", Path.home() / ".cache/huggingface"))
    cached = cache.exists()
    checks.append(
        (
            "Model",
            model_local or cached,
            "local path/cache" if model_local or cached else "downloads on first use",
        )
    )
    lines = [f"{'PASS' if ok else 'FAIL'}  {name}: {detail}" for name, ok, detail in checks]
    required = [ok for name, ok, _ in checks if name != "Model"]
    return all(required), lines
