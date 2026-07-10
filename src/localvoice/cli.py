from __future__ import annotations

import argparse
import json
import sys

from .clipboard import copy_text
from .config import Settings
from .doctor import report
from .hypr_config import write_config
from .hyprland import HyprlandController, is_hyprland_wayland
from .ipc import send_command

COMMANDS = {
    "ptt-start",
    "ptt-stop",
    "toggle",
    "start",
    "stop",
    "continuous-start",
    "continuous-stop",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="localvoice")
    parser.add_argument("--gui", action="store_true", help="open the graphical interface")
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(COMMANDS | {"doctor", "clipboard-test", "hyprland-test", "hyprland-config"}),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.gui or args.command is None:
        if not is_hyprland_wayland():
            print("LocalVoice requires Hyprland running on Wayland", file=sys.stderr)
            return 2
        from .gui import run_gui

        return run_gui(Settings.load())
    if args.command == "doctor":
        healthy, lines = report()
        print("\n".join(lines))
        return 0 if healthy else 1
    if args.command == "clipboard-test":
        copy_text("LocalVoice clipboard test")
        print("Clipboard test copied successfully")
        return 0
    if args.command == "hyprland-test":
        if not is_hyprland_wayland():
            print("Hyprland Wayland session variables are incomplete", file=sys.stderr)
            return 1
        controller = HyprlandController()
        active_target = controller.capture_target()
        print(json.dumps({"hyprland": True, "active_target_available": active_target is not None}))
        return 0
    if args.command == "hyprland-config":
        try:
            print(write_config())
            return 0
        except FileExistsError as exc:
            print(exc, file=sys.stderr)
            return 1
    target: str | None = None
    if args.command in {"ptt-start", "toggle", "start"} and is_hyprland_wayland():
        captured = HyprlandController().capture_target()
        target = captured.address if captured else None
    if send_command(args.command, target):
        return 0
    print("LocalVoice GUI is not running; start it with: localvoice --gui", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
