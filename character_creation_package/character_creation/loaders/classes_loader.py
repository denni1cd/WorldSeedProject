from pathlib import Path
from typing import Any, List
import yaml


def load_class_catalog(path: Path) -> List[Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
