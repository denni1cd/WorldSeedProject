from __future__ import annotations
from typing import Dict, Any


class DataValidationError(Exception): ...


def validate_stats(stats: Dict[str, Any]) -> None:
    for k, v in stats.items():
        if "initial" not in v or "xp_to_next" not in v:
            raise DataValidationError(f"stat {k} missing keys")
        float(v["initial"])
        float(v["xp_to_next"])


def validate_classes(catalog: Dict[str, Any]) -> None:
    classes = catalog.get("classes", [])
    if not isinstance(classes, list) or not classes:
        raise DataValidationError("classes list missing/empty")
    for c in classes:
        if "id" not in c or "grants_stats" not in c or "grants_abilities" not in c:
            raise DataValidationError(f"class invalid: {c}")


def validate_traits(traits: Dict[str, Any]) -> None:
    t = traits.get("traits", {})
    if not t:
        raise DataValidationError("traits empty")
    for k, v in t.items():
        if "desc" not in v:
            raise DataValidationError(f"trait {k} missing desc")


def validate_slots(slots: Dict[str, Any]) -> None:
    s = slots.get("slots", slots)
    if not s:
        raise DataValidationError("slots empty")
    for sid, meta in s.items():
        if not isinstance(meta, dict) or "display" not in meta or "cat" not in meta:
            raise DataValidationError(f"slot {sid} missing display/cat")


def validate_items(items: Any, slots: Dict[str, Any]) -> None:
    s = slots.get("slots", slots)
    if isinstance(items, dict) and "items" in items:
        iterable = items["items"]
    elif isinstance(items, list):
        iterable = items
    elif isinstance(items, dict):
        iterable = list(items.values())
    else:
        raise DataValidationError("items catalog invalid")

    for it in iterable:
        if "id" not in it or "name" not in it or "slot" not in it:
            raise DataValidationError(f"item missing keys: {it}")
        # slot may be id(s) or category; basic sanity
        allowed = it["slot"] if isinstance(it["slot"], list) else [it["slot"]]
        if not any(a in s or a in {m.get("cat") for m in s.values()} for a in allowed):
            raise DataValidationError(f"item {it['id']} slot/category not recognized")
