from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


class LocalTranscriber:
    def __init__(
        self,
        model_name: str,
        compute_type: str = "int8",
        language: str | None = "en",
        factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self.compute_type = compute_type
        self.language = language
        self._factory = factory
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            factory = self._factory
            if factory is None:
                from faster_whisper import WhisperModel  # type: ignore[import-untyped]

                factory = WhisperModel
            self._model = factory(self.model_name, device="cpu", compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        segments, _ = self._load().transcribe(
            str(audio_path), language=self.language, vad_filter=True, beam_size=5
        )
        return " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        ).strip()
