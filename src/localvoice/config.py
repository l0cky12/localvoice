from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    model: str = "small.en"
    compute_type: str = "int8"
    language: str | None = "en"
    input_device: str | None = None
    output_device: str | None = None
    paste_modifiers: str = "CTRL"
    paste_key: str = "V"

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        values: dict[str, object] = {}
        config_path = path or Path.home() / ".config/localvoice/config.toml"
        if config_path.is_file():
            with config_path.open("rb") as handle:
                values.update(tomllib.load(handle))
        env_map = {
            "model": os.getenv("LOCALVOICE_MODEL"),
            "compute_type": os.getenv("LOCALVOICE_COMPUTE_TYPE"),
            "language": os.getenv("LOCALVOICE_LANGUAGE"),
        }
        values.update({key: value for key, value in env_map.items() if value is not None})
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in values.items() if key in allowed})  # type: ignore[arg-type]
