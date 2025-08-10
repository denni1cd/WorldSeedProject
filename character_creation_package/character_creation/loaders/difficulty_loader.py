from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml


def load_difficulty(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("balance", {"current": "normal", "difficulties": {"normal": {}}})
