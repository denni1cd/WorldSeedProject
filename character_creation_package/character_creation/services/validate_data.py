from __future__ import annotations
from typing import Dict, Any, Set


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


# New validators for races and appearance/ranges/creation limits
def validate_races(catalog: Dict[str, Any]) -> None:
    races = catalog.get("races", [])
    if not isinstance(races, list) or not races:
        raise DataValidationError("races list missing/empty")
    seen: Set[str] = set()
    for r in races:
        if not isinstance(r, dict):
            raise DataValidationError("race entry not a dict")
        rid = r.get("id")
        name = r.get("name")
        if not rid or not isinstance(rid, str):
            raise DataValidationError("race missing id")
        if rid in seen:
            raise DataValidationError(f"duplicate race id {rid}")
        seen.add(rid)
        if not name or not isinstance(name, str):
            raise DataValidationError(f"race {rid} missing name")
        gs = r.get("grants_stats", {})
        if not isinstance(gs, dict):
            raise DataValidationError(f"race {rid} grants_stats not a dict")
        for k, v in gs.items():
            try:
                float(v)
            except Exception:
                raise DataValidationError(
                    f"race {rid} invalid grants_stats value for {k}"
                )
        ga = r.get("grants_abilities", [])
        if not isinstance(ga, list):
            raise DataValidationError(f"race {rid} grants_abilities not a list")


def validate_appearance_fields(fields: Dict[str, Any]) -> None:
    # Allow either {'fields': {...}} or direct mapping
    spec = fields.get("fields", fields) if isinstance(fields, dict) else {}
    if not isinstance(spec, dict) or not spec:
        raise DataValidationError("appearance fields empty/invalid")
    for fid, meta in spec.items():
        if not isinstance(meta, dict):
            raise DataValidationError(f"appearance field {fid} not a dict")
        ftype = meta.get("type")
        if ftype not in ("enum", "float", "number", "int", "any"):
            raise DataValidationError(f"appearance field {fid} invalid type {ftype}")
        if "default" not in meta:
            raise DataValidationError(f"appearance field {fid} missing default")
        # For enum fields, accept 'table' or 'table_ref' (which may be a dict or str)
        if ftype == "enum":
            has_table = "table" in meta or "table_ref" in meta
            if not has_table:
                raise DataValidationError(
                    f"appearance enum field {fid} missing table/table_ref"
                )
        # For numeric fields, accept 'range' or 'range_ref'
        if ftype in {"float", "number", "int"}:
            has_range = "range" in meta or "range_ref" in meta
            if not has_range:
                raise DataValidationError(
                    f"appearance float field {fid} missing range/range_ref"
                )


def validate_appearance_table(values: Any, table_name: str) -> None:
    # Accept either a raw list of scalars or a mapping with key 'values'
    if isinstance(values, dict) and "values" in values:
        values = values.get("values")
    if not isinstance(values, list) or not all(
        isinstance(x, (str, int, float)) or x is None for x in values
    ):
        raise DataValidationError(
            f"appearance table {table_name} must be a list of scalars"
        )


def validate_numeric_range(rng: Dict[str, Any], range_name: str) -> None:
    # Accept either direct range dict or mapping with key 'range'
    if isinstance(rng, dict) and "range" in rng:
        rng = rng.get("range")
    if not isinstance(rng, dict):
        raise DataValidationError(f"range {range_name} not a dict")
    has_minmax = "min" in rng and "max" in rng
    has_stats = "mean" in rng and "sd" in rng
    if not (has_minmax or has_stats):
        raise DataValidationError(
            f"range {range_name} must have (min,max) or (mean,sd)"
        )
    if has_minmax and float(rng["min"]) > float(rng["max"]):
        raise DataValidationError(f"range {range_name} min>max")


def validate_creation_limits(limits: Dict[str, Any]) -> None:
    lm = limits.get("limits", limits)
    if not isinstance(lm, dict):
        raise DataValidationError("creation limits invalid")
    if "traits_max" in lm and int(lm["traits_max"]) < 0:
        raise DataValidationError("traits_max must be >= 0")
    if "edit_numeric_step" in lm:
        step = float(lm["edit_numeric_step"])
        if step <= 0:
            raise DataValidationError("edit_numeric_step must be > 0")


# --- New helpers for content packs ---
def validate_no_duplicate_ids(list_of_dicts: list, kind: str) -> None:
    seen: Set[str] = set()
    for entry in list_of_dicts:
        if not isinstance(entry, dict):
            raise DataValidationError(f"{kind} entry not a dict: {entry}")
        eid = entry.get("id")
        if not isinstance(eid, str) or not eid:
            raise DataValidationError(f"{kind} entry missing id: {entry}")
        if eid in seen:
            raise DataValidationError(f"duplicate {kind} id {eid}")
        seen.add(eid)


def validate_merged_catalogs(merged: Dict[str, Any]) -> None:
    if not isinstance(merged, dict):
        raise DataValidationError("merged catalog must be a dict")
    if "classes" in merged and isinstance(merged["classes"], list):
        validate_no_duplicate_ids(merged["classes"], "class")
    if "races" in merged and isinstance(merged["races"], list):
        validate_no_duplicate_ids(merged["races"], "race")
    if "items" in merged and isinstance(merged["items"], list):
        validate_no_duplicate_ids(merged["items"], "item")
    # traits is a dict; keys uniqueness is inherent in Python dict
    if "appearance_tables" in merged:
        tables = merged["appearance_tables"]
        if not isinstance(tables, dict):
            raise DataValidationError("appearance_tables must be a dict")
        for tname, values in tables.items():
            if not isinstance(values, list):
                raise DataValidationError(f"appearance table {tname} must be a list")
            for v in values:
                if not isinstance(v, (str, int, float)) and v is not None:
                    raise DataValidationError(
                        f"appearance table {tname} contains non-scalar value {v!r}"
                    )
