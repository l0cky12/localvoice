from __future__ import annotations

from localvoice.hyprland import (
    HyprlandController,
    WindowTarget,
    is_hyprland_wayland,
    parse_clients,
    parse_window,
)


def test_hyprland_detection_requires_all_variables() -> None:
    env = {
        "XDG_SESSION_TYPE": "wayland",
        "HYPRLAND_INSTANCE_SIGNATURE": "abc",
        "WAYLAND_DISPLAY": "wayland-1",
    }
    assert is_hyprland_wayland(env)
    assert not is_hyprland_wayland({**env, "XDG_SESSION_TYPE": "x11"})
    assert not is_hyprland_wayland({**env, "HYPRLAND_INSTANCE_SIGNATURE": ""})


def test_hyprctl_json_parsing() -> None:
    assert parse_window({"address": "0xabc123", "class": "kitty"}) == WindowTarget(
        "0xabc123", "kitty"
    )
    assert parse_window({"address": "not-an-address"}) is None
    assert parse_clients([{"address": "0x1"}, {"address": "0x2"}]) == {"0x1", "0x2"}


def test_localvoice_window_is_not_a_target() -> None:
    controller = HyprlandController(
        json_runner=lambda _args: {"address": "0x1", "class": "localvoice"}
    )
    assert controller.capture_target() is None


def test_focus_restore_validates_client_and_uses_no_text_arguments() -> None:
    calls: list[list[str]] = []
    controller = HyprlandController(
        json_runner=lambda _args: [{"address": "0xabc", "class": "editor"}],
        command_runner=lambda args: calls.append(list(args)),
    )
    assert controller.restore_and_paste(WindowTarget("0xabc", "editor"), "CTRL", "V")
    assert calls == [
        ["hyprctl", "dispatch", "focuswindow", "address:0xabc"],
        ["hyprctl", "dispatch", "sendshortcut", "CTRL", "V", "address:0xabc"],
    ]


def test_focus_restore_fails_if_window_disappeared() -> None:
    controller = HyprlandController(json_runner=lambda _args: [], command_runner=lambda _args: None)
    assert not controller.restore_and_paste(WindowTarget("0xabc", "editor"), "CTRL", "V")
