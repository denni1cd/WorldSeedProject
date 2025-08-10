from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_race_catalog(path: str | Path) -> Dict[str, Any]:
    """
    Load the race catalog from YAML. Always return a dict with key 'races' mapping to a list.
    If the YAML is missing or malformed, fail gracefully and return {'races': []}.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return {"races": []}
        races = data.get("races")
        if isinstance(races, list):
            return {"races": races}
        return {"races": []}
    except Exception:
        return {"races": []}
