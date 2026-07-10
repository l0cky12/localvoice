from __future__ import annotations

from dataclasses import replace
from typing import Any

from .config import Settings
from .ipc import CommandServer
from .pipewire import inputs, list_devices, outputs
from .service import DictationService


def run_gui(settings: Settings | None = None) -> int:
    from PySide6.QtCore import QObject, Qt, Signal, Slot
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    class Bridge(QObject):
        text = Signal(str)
        status = Signal(str)
        command = Signal(str, object)

    existing_app = QApplication.instance()
    app = existing_app if isinstance(existing_app, QApplication) else QApplication([])
    app.setApplicationName("LocalVoice")
    app.setDesktopFileName("localvoice")
    bridge = Bridge()
    active_settings = settings or Settings.load()
    service = DictationService(active_settings, bridge.text.emit, bridge.status.emit)

    window = QMainWindow()
    window.setWindowTitle("LocalVoice")
    window.setProperty("class", "localvoice")
    central = QWidget()
    layout = QVBoxLayout(central)
    status = QLabel("Idle")
    status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    transcript = QTextEdit()
    transcript.setReadOnly(True)
    transcript.setPlaceholderText("Successful transcriptions remain here and in the clipboard.")
    devices = list_devices()
    input_box, output_box = QComboBox(), QComboBox()
    input_box.addItem("Default PipeWire input", None)
    output_box.addItem("Default PipeWire output", None)
    for device in inputs(devices):
        input_box.addItem(device.name, device.identifier)
    for device in outputs(devices):
        output_box.addItem(device.name, device.identifier)
    layout.addWidget(QLabel("Input device"))
    layout.addWidget(input_box)
    layout.addWidget(QLabel("Output device (Piper TTS)"))
    layout.addWidget(output_box)
    buttons = QHBoxLayout()
    record = QPushButton("Start / Stop")
    continuous = QPushButton("Continuous")
    continuous.setCheckable(True)
    buttons.addWidget(record)
    buttons.addWidget(continuous)
    layout.addLayout(buttons)
    layout.addWidget(status)
    layout.addWidget(transcript)
    window.setCentralWidget(central)

    bridge.text.connect(transcript.setPlainText)
    bridge.status.connect(status.setText)

    @Slot(str, object)
    def handle(command: str, target: Any = None) -> None:
        try:
            service.settings = replace(
                service.settings,
                input_device=input_box.currentData(),
                output_device=output_box.currentData(),
            )
            if command in {"ptt-start", "start"}:
                service.start(target)
            elif command in {"ptt-stop", "stop"}:
                service.stop()
            elif command == "toggle":
                service.toggle(target)
            elif command == "continuous-start":
                service.continuous_start()
            elif command == "continuous-stop":
                service.continuous_stop()
        except Exception as exc:
            status.setText(f"Error: {exc}")

    bridge.command.connect(handle)
    record.clicked.connect(lambda: handle("toggle"))
    continuous.toggled.connect(
        lambda checked: handle("continuous-start" if checked else "continuous-stop")
    )
    server = CommandServer(lambda command, target: bridge.command.emit(command, target))
    server.start()
    app.aboutToQuit.connect(server.stop)
    window.resize(650, 440)
    window.show()
    return app.exec()
