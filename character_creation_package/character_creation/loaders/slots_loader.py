from pathlib import Path
from typing import Any, Dict
import yaml


def load_slot_template(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
