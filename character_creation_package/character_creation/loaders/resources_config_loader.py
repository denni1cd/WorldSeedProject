from __future__ import annotations
from pathlib import Path
import yaml
from typing import Dict, Any


def load_resource_config(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("resources", {})
