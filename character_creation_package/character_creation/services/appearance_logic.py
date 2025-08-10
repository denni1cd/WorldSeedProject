from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def _read_yaml(path: Path) -> Dict[str, Any] | List[Any] | None:
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def get_enum_values(
    field_id: str,
    fields_spec: Dict[str, Any],
    base_dir: Path,
    extra_tables: Dict[str, List[Any]] | None = None,
) -> List[str]:
    """
    If fields_spec[field_id]['type'] == 'enum', read its 'table' yaml under base_dir/'tables'.
    Return list of allowed string values. If missing, return [].
    """

    # Support both top-level and nested under 'fields'
    spec = fields_spec.get("fields", fields_spec)
    meta = spec.get(field_id, {}) if isinstance(spec, dict) else {}
    if not isinstance(meta, dict) or meta.get("type") != "enum":
        return []

    ref = meta.get("table_ref") or meta.get("table")
    file_ref = None
    if isinstance(ref, dict):
        file_ref = ref.get("file")
    elif isinstance(ref, str):
        file_ref = ref

    if not file_ref:
        return []

    table_path = (base_dir / file_ref).resolve()
    data = _read_yaml(table_path)
    if isinstance(data, dict) and "values" in data:
        values = data.get("values") or []
    elif isinstance(data, list):
        values = data
    else:
        values = []

    # Augment with extra tables if provided. Use the stem of the file as table name key.
    # Also accept common singular/plural variants for convenience.
    if isinstance(file_ref, str):
        stem = Path(file_ref).stem
    else:
        stem = ""
    if extra_tables:
        candidates = [stem]
        # simple singular/plural normalization
        if stem.endswith("s"):
            candidates.append(stem[:-1])
        else:
            candidates.append(stem + "s")
        for key in candidates:
            pack_vals = extra_tables.get(key)
            if isinstance(pack_vals, list):
                # union preserve order: base first then unique from pack
                seen = set(values)
                for v in pack_vals:
                    if v not in seen:
                        values.append(v)
                        seen.add(v)

    # Coerce to strings except for explicit None/null
    result: List[str] = []
    for v in values:
        if v is None:
            result.append("null")
        else:
            result.append(str(v))
    return result


def get_numeric_bounds(
    field_id: str, fields_spec: Dict[str, Any], base_dir: Path
) -> Tuple[float, float] | None:
    """
    If type == 'float', read its 'range' yaml under base_dir/'ranges' to extract (min, max).
    If only mean/sd are present, derive a reasonable min/max (e.g., mean ± 3*sd).
    Return (min, max) or None if not available.
    """

    spec = fields_spec.get("fields", fields_spec)
    meta = spec.get(field_id, {}) if isinstance(spec, dict) else {}
    if not isinstance(meta, dict) or meta.get("type") not in {"float", "number", "int"}:
        return None

    range_block: Dict[str, Any] | None = None

    # Direct inline range
    if isinstance(meta.get("range"), dict):
        range_block = meta.get("range")

    # Range ref to file
    ref = meta.get("range_ref") or meta.get("range_file")
    file_ref = None
    if isinstance(ref, dict):
        file_ref = ref.get("file")
    elif isinstance(ref, str):
        file_ref = ref
    if file_ref and not range_block:
        path = (base_dir / file_ref).resolve()
        data = _read_yaml(path)
        if isinstance(data, dict):
            range_block = data.get("range") or data

    if not isinstance(range_block, dict):
        return None

    min_v = range_block.get("min")
    max_v = range_block.get("max")
    mean = range_block.get("mean")
    sd = range_block.get("sd") or range_block.get("std")

    if min_v is not None and max_v is not None:
        try:
            return float(min_v), float(max_v)
        except Exception:
            pass

    if mean is not None and sd is not None:
        try:
            mean_f = float(mean)
            sd_f = float(sd)
            return mean_f - 3 * sd_f, mean_f + 3 * sd_f
        except Exception:
            return None

    return None


def coerce_numeric(value: float, min_v: float, max_v: float) -> float:
    """Clamp a numeric value to [min_v, max_v]."""
    try:
        v = float(value)
    except Exception:
        v = min_v
    if v < min_v:
        return float(min_v)
    if v > max_v:
        return float(max_v)
    return float(v)


def default_for_field(field_id: str, fields_spec: Dict[str, Any], defaults: Dict[str, Any]) -> Any:
    """Return defaults.get(field_id, fields_spec[field_id]['default'])."""
    spec = fields_spec.get("fields", fields_spec)
    meta = spec.get(field_id, {}) if isinstance(spec, dict) else {}
    if field_id in (defaults or {}):
        return defaults[field_id]
    return meta.get("default")
