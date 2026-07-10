from __future__ import annotations

import pytest

pytest.importorskip("PySide6")


def test_gui_starts_offscreen_and_exits(monkeypatch) -> None:
    from PySide6.QtCore import QTimer

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        pytest.skip(f"Qt runtime libraries unavailable: {exc}")

    from localvoice import gui

    monkeypatch.setattr(gui, "list_devices", lambda: [])
    monkeypatch.setattr(gui.CommandServer, "start", lambda _self: None)
    monkeypatch.setattr(gui.CommandServer, "stop", lambda _self: None)
    QTimer.singleShot(50, QApplication.quit)
    assert gui.run_gui() == 0
