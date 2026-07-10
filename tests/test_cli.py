from __future__ import annotations

from pathlib import Path

from localvoice import cli


def test_doctor_cli(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "report", lambda: (True, ["PASS  mocked"]))
    assert cli.main(["doctor"]) == 0
    assert "PASS  mocked" in capsys.readouterr().out


def test_action_cli_sends_captured_target(monkeypatch) -> None:
    class Controller:
        def capture_target(self):
            return type("Target", (), {"address": "0xabc"})()

    sent: list[tuple[str, str | None]] = []
    monkeypatch.setattr(cli, "is_hyprland_wayland", lambda: True)
    monkeypatch.setattr(cli, "HyprlandController", Controller)
    monkeypatch.setattr(
        cli, "send_command", lambda command, target: sent.append((command, target)) or True
    )
    assert cli.main(["ptt-start"]) == 0
    assert sent == [("ptt-start", "0xabc")]


def test_hyprland_config_does_not_modify_main_config(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "localvoice.conf"
    monkeypatch.setattr(cli, "write_config", lambda: destination)
    assert cli.main(["hyprland-config"]) == 0
