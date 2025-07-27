from pathlib import Path
from typing import Any, Dict
import yaml


def load_resources_default():
    resources_path = Path(__file__).parent.parent / "data" / "resources.yaml"
    return load_resources(resources_path)


def load_resources(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
