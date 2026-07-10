from __future__ import annotations

import wave
from pathlib import Path

from localvoice.vad import ContinuousListener


def test_vad_emits_valid_local_wave() -> None:
    emitted: list[Path] = []
    listener = ContinuousListener(emitted.append)
    listener._emit([b"\x00\x00" * 480] * 15)
    assert len(emitted) == 1
    with wave.open(str(emitted[0]), "rb") as stream:
        assert stream.getframerate() == 16000
        assert stream.getnchannels() == 1
    emitted[0].unlink()
    emitted[0].parent.rmdir()
