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


class _ChunkedStream:
    """Pipe-like stream that returns short reads before delivering a full frame."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    def read(self, _size: int) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""


def test_read_frame_accumulates_partial_pipe_reads() -> None:
    listener = ContinuousListener(lambda _path: None)
    stream = _ChunkedStream([b"\x01" * 400, b"\x02" * 560])
    frame = listener._read_frame(stream, 960)
    assert len(frame) == 960
    assert frame == b"\x01" * 400 + b"\x02" * 560


def test_read_frame_stops_on_eof() -> None:
    listener = ContinuousListener(lambda _path: None)
    stream = _ChunkedStream([b"\x00" * 100])
    assert listener._read_frame(stream, 960) == b"\x00" * 100
