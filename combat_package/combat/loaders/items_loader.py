from __future__ import annotations
from pathlib import Path
import yaml


def load_items(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"items": {}}
    with open(p, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("items", {})
    return data
