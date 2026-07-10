from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def speak(text: str, model: Path, output_target: str | None = None) -> None:
    if not text or not model.is_file():
        raise ValueError("Text and an existing Piper model are required")
    with tempfile.TemporaryDirectory(prefix="localvoice-tts-") as directory:
        audio = Path(directory) / "speech.wav"
        subprocess.run(  # noqa: S603 - fixed argv, shell explicitly disabled
            ["piper", "--model", str(model), "--output_file", str(audio)],  # noqa: S607
            input=text.encode(),
            check=True,
            timeout=120,
            shell=False,
        )
        args = ["pw-play"]
        if output_target:
            args.extend(["--target", output_target])
        args.append(str(audio))
        subprocess.run(args, check=True, timeout=120, shell=False)  # noqa: S603
