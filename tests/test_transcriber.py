from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from localvoice.transcriber import LocalTranscriber


@dataclass
class Segment:
    text: str


class FakeModel:
    def transcribe(self, path: str, **kwargs: Any) -> tuple[list[Segment], object]:
        assert Path(path).is_file()
        assert kwargs["vad_filter"] is True
        return [Segment(" hello "), Segment("world")], object()


def test_local_transcription(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"audio")
    factory_calls: list[tuple[str, dict[str, Any]]] = []

    def factory(model: str, **kwargs: Any) -> FakeModel:
        factory_calls.append((model, kwargs))
        return FakeModel()

    transcriber = LocalTranscriber("local-model", factory=factory)
    assert transcriber.transcribe(audio) == "hello world"
    assert factory_calls == [("local-model", {"device": "cpu", "compute_type": "int8"})]
