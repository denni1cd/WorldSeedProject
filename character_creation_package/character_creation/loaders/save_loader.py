from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def save_character(character: Any, path: str | Path) -> None:
    """Saves a character object to YAML."""
    if not isinstance(path, Path):
        path = Path(path)
    data = character.__dict__
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


def load_character(path: str | Path, cls: type) -> Any:
    """Loads a character from YAML into the provided class."""
    if not isinstance(path, Path):
        path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return cls(**data)
