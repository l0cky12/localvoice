from __future__ import annotations

import json
import os
import socket
import threading
from collections.abc import Callable
from pathlib import Path


def socket_path() -> Path:
    runtime_value = os.getenv("XDG_RUNTIME_DIR")
    if not runtime_value:
        raise RuntimeError("XDG_RUNTIME_DIR is required for LocalVoice IPC")
    runtime = Path(runtime_value)
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    return runtime / "localvoice.sock"


def send_command(command: str, target: str | None = None) -> bool:
    payload = json.dumps({"command": command, "target": target}).encode()
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(2)
            client.connect(str(socket_path()))
            client.sendall(payload)
        return True
    except (OSError, RuntimeError):
        return False


class CommandServer:
    def __init__(self, callback: Callable[[str, str | None], None]) -> None:
        self.callback = callback
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        path = socket_path()
        path.unlink(missing_ok=True)
        self._socket = socket.socket(socket.AF_UNIX)
        self._socket.bind(str(path))
        os.chmod(path, 0o600)
        self._socket.listen(5)
        self._socket.settimeout(0.5)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        assert self._socket is not None
        while not self._stop.is_set():
            try:
                connection, _ = self._socket.accept()
            except TimeoutError:
                continue
            with connection:
                try:
                    data = json.loads(connection.recv(4096))
                    command, target = data.get("command"), data.get("target")
                    if isinstance(command, str) and (target is None or isinstance(target, str)):
                        self.callback(command, target)
                except (json.JSONDecodeError, OSError):
                    continue

    def stop(self) -> None:
        self._stop.set()
        if self._socket:
            self._socket.close()
        socket_path().unlink(missing_ok=True)
