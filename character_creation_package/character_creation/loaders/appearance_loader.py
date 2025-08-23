from pathlib import Path
from typing import Any, Dict, List
import yaml


def load_fields():
    # Default path to fields.yaml
    fields_path = Path(__file__).parent.parent / "data" / "appearance" / "fields.yaml"
    return load_appearance_fields(fields_path)


def load_defaults() -> Dict[str, Any]:
    """Backward-compatible alias to load defaults from default path."""
    defaults_path = Path(__file__).parent.parent / "data" / "appearance" / "defaults.yaml"
    return load_appearance_defaults(defaults_path)


def load_appearance_fields(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_appearance_defaults(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_enum(table_ref: str, base_dir: Path) -> List[Any]:
    table_path = (base_dir / table_ref).resolve()
    with open(table_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_range(range_ref: str, base_dir: Path) -> Dict[str, Any]:
    range_path = (base_dir / range_ref).resolve()
    with open(range_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
