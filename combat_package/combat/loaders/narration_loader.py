from __future__ import annotations
from pathlib import Path
import yaml


def load_narration(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"templates": {}, "verbs": {}, "adjectives": {}, "miss": []}
    with open(p, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("templates", {})
    data.setdefault("verbs", {})
    data.setdefault("adjectives", {})
    data.setdefault("miss", [])
    return data
