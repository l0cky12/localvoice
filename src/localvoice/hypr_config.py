from __future__ import annotations

from pathlib import Path

CONFIG = """# LocalVoice — generated file. Source manually from hyprland.conf.
# Push-to-talk: hold Ctrl+Alt+Space.
bind = CTRL ALT, SPACE, exec, localvoice ptt-start
bindr = CTRL ALT, SPACE, exec, localvoice ptt-stop
# Optional examples:
# bind = CTRL ALT, D, exec, localvoice toggle
# bind = CTRL ALT SHIFT, D, exec, localvoice continuous-start
# bind = CTRL ALT SHIFT, S, exec, localvoice continuous-stop
"""


def write_config(path: Path | None = None, *, overwrite: bool = False) -> Path:
    destination = path or Path.home() / ".config/hypr/localvoice.conf"
    if destination.exists() and not overwrite:
        if destination.read_text(encoding="utf-8") == CONFIG:
            return destination
        raise FileExistsError(f"Refusing to overwrite existing personal config: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(CONFIG, encoding="utf-8")
    return destination
