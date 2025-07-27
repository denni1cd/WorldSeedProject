from pathlib import Path
from typing import Any, Dict
import yaml


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(base_dir: Path, ref: str) -> Path:
    return (base_dir / ref).resolve()
