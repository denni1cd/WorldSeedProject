from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_packs_config(path: str | Path) -> Dict[str, Any]:
    """
    Load content packs configuration from YAML. If missing or invalid, return defaults.

    Expected schema:
    {
      enabled: [pack_name, ...],
      merge: { on_conflict: "skip" | "override" | "error" }
    }
    """
    path = Path(path)
    try:
        if not path.exists():
            return {"enabled": [], "merge": {"on_conflict": "skip"}}
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        enabled = data.get("enabled") or []
        if not isinstance(enabled, list):
            enabled = []
        merge = data.get("merge") or {}
        if not isinstance(merge, dict):
            merge = {}
        on_conflict = merge.get("on_conflict") or "skip"
        if on_conflict not in {"skip", "override", "error"}:
            on_conflict = "skip"
        return {"enabled": list(enabled), "merge": {"on_conflict": on_conflict}}
    except Exception:
        return {"enabled": [], "merge": {"on_conflict": "skip"}}


def _read_yaml_optional(path: Path) -> Any:
    try:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def load_pack_dir(pack_dir: Path) -> Dict[str, Any]:
    """
    Load a single content pack directory structure into a catalog-like dict.
    Recognized files (all optional):
      classes.yaml -> {"classes": [...]}
      traits.yaml -> {"traits": {...}}
      races.yaml -> {"races": [...]}
      items.yaml -> {"items": [...] or {items: [...]}}
      appearance/tables/*.yaml -> {"appearance_tables": {name: [values...]}}
    """
    result: Dict[str, Any] = {}
    # Classes
    classes_path = pack_dir / "classes.yaml"
    data = _read_yaml_optional(classes_path)
    if isinstance(data, dict) and isinstance(data.get("classes"), list):
        result["classes"] = list(data["classes"])  # shallow copy
    elif isinstance(data, list):
        result["classes"] = list(data)

    # Traits
    traits_path = pack_dir / "traits.yaml"
    data = _read_yaml_optional(traits_path)
    if isinstance(data, dict):
        traits = data.get("traits", data)
        if isinstance(traits, dict):
            result["traits"] = dict(traits)

    # Races
    races_path = pack_dir / "races.yaml"
    data = _read_yaml_optional(races_path)
    if isinstance(data, dict) and isinstance(data.get("races"), list):
        result["races"] = list(data["races"])  # shallow copy
    elif isinstance(data, list):
        result["races"] = list(data)

    # Items
    items_path = pack_dir / "items.yaml"
    data = _read_yaml_optional(items_path)
    if isinstance(data, dict):
        if isinstance(data.get("items"), list):
            result["items"] = list(data.get("items"))
        else:
            # Some repos use dict keyed by id; normalize to list
            # Accept either a list at top-level or dict of id->item
            items_block = data
            if isinstance(items_block, dict):
                # If values look like items (dicts with id), flatten
                vals = list(items_block.values())
                if vals and isinstance(vals[0], dict) and ("id" in vals[0] or "name" in vals[0]):
                    result["items"] = vals
    elif isinstance(data, list):
        result["items"] = list(data)

    # Appearance tables
    app_tables_dir = pack_dir / "appearance" / "tables"
    if app_tables_dir.exists() and app_tables_dir.is_dir():
        tables: Dict[str, List[Any]] = {}
        for child in sorted(app_tables_dir.glob("*.yaml")):
            loaded = _read_yaml_optional(child)
            values: List[Any] | None = None
            if isinstance(loaded, dict) and "values" in loaded:
                maybe_values = loaded.get("values")
                if isinstance(maybe_values, list):
                    values = maybe_values
            elif isinstance(loaded, list):
                values = loaded
            if values is not None:
                tables[child.stem] = list(values)
        if tables:
            result["appearance_tables"] = tables

    return result


def _merge_indexed_lists(
    base: List[Dict[str, Any]] | None,
    incoming: List[Dict[str, Any]] | None,
    on_conflict: str,
) -> List[Dict[str, Any]]:
    base = list(base or [])
    if not incoming:
        return base
    # Build index for base by id
    index: Dict[str, int] = {}
    for i, entry in enumerate(base):
        if isinstance(entry, dict) and "id" in entry:
            index[str(entry["id"])] = i
    for entry in incoming:
        if not isinstance(entry, dict) or "id" not in entry:
            continue
        eid = str(entry["id"])
        if eid in index:
            if on_conflict == "skip":
                continue
            if on_conflict == "error":
                raise ValueError(f"Duplicate id '{eid}' during merge")
            # override
            base[index[eid]] = entry
        else:
            base.append(entry)
            index[eid] = len(base) - 1
    return base


def _merge_traits(
    base: Dict[str, Any] | None, incoming: Dict[str, Any] | None, on_conflict: str
) -> Dict[str, Any]:
    base = dict(base or {})
    incoming = dict(incoming or {})
    for tid, meta in incoming.items():
        if tid in base:
            if on_conflict == "skip":
                continue
            if on_conflict == "error":
                raise ValueError(f"Duplicate trait id '{tid}' during merge")
        base[tid] = meta
    return base


def _union_preserve_order(base_vals: List[Any] | None, new_vals: List[Any] | None) -> List[Any]:
    result: List[Any] = []
    seen: set[Any] = set()
    for arr in (base_vals or [], new_vals or []):
        for v in arr:
            key = v
            if key not in seen:
                seen.add(key)
                result.append(v)
    return result


def merge_catalogs(
    base: Dict[str, Any], pack: Dict[str, Any], on_conflict: str = "skip"
) -> Dict[str, Any]:
    """
    Merge two catalogs following rules described in the spec.
    Return a new merged dict with any present keys.
    """
    result: Dict[str, Any] = {}

    # classes/races/items are lists of dicts with id
    for key in ("classes", "races", "items"):
        if key in base or key in pack:
            result[key] = _merge_indexed_lists(base.get(key), pack.get(key), on_conflict)

    # traits is a mapping of id -> meta; may be nested under 'traits'
    base_traits = base.get("traits")
    pack_traits = pack.get("traits")
    if base_traits is not None or pack_traits is not None:
        result["traits"] = _merge_traits(base_traits or {}, pack_traits or {}, on_conflict)

    # appearance_tables: dict name -> list of scalars; union lists
    base_tables = base.get("appearance_tables") or {}
    pack_tables = pack.get("appearance_tables") or {}
    if base_tables or pack_tables:
        merged_tables: Dict[str, List[Any]] = {}
        for tname in sorted(set(base_tables.keys()) | set(pack_tables.keys())):
            merged_tables[tname] = _union_preserve_order(
                base_tables.get(tname), pack_tables.get(tname)
            )
        result["appearance_tables"] = merged_tables

    return result


def load_and_merge_enabled_packs(base_root: Path, packs_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    For each pack in cfg["enabled"], load its directory under base_root/content_packs/<name>,
    and merge into an accumulator according to cfg["merge"]["on_conflict"].
    Returns a single catalog-like dict with any of the supported keys present.
    """
    enabled: List[str] = list((packs_cfg or {}).get("enabled") or [])
    on_conflict = ((packs_cfg or {}).get("merge") or {}).get("on_conflict", "skip")
    if on_conflict not in {"skip", "override", "error"}:
        on_conflict = "skip"

    acc: Dict[str, Any] = {}
    # Prefer character/content_packs, then backend/content_packs, else legacy content_packs at root
    char_content_dir = base_root / "character" / "content_packs"
    back_content_dir = base_root / "backend" / "content_packs"
    legacy_content_dir = base_root / "content_packs"
    if char_content_dir.exists():
        search_dir = char_content_dir
    elif back_content_dir.exists():
        search_dir = back_content_dir
    else:
        search_dir = legacy_content_dir
    for name in enabled:
        pack_dir = search_dir / name
        pack_data = load_pack_dir(pack_dir)
        # Merge pack_data into acc using merge_catalogs, with acc as base and pack as overlay
        acc = merge_catalogs(acc, pack_data, on_conflict)
    return acc
