from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .abilities_loader import load_abilities
from .damage_types_loader import load_damage_types
from .narration_loader import load_narration
from .body_parts_loader import load_body_parts
from .status_effects_loader import load_status_effects
import yaml

MERGE_KEYS = ("abilities", "damage_types", "narration", "body_parts", "status_effects")


def _read_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _dict_by_id(seq: List[dict], key: str = "id") -> Dict[str, dict]:
    out = {}
    for item in seq or []:
        iid = item.get(key)
        if iid is not None and iid not in out:
            out[iid] = item
    return out


def _merge_lists(
    base: List[dict], add: List[dict], policy: str, what: str, errors: List[str]
) -> List[dict]:
    a = _dict_by_id(base or [])
    b = _dict_by_id(add or [])
    for k, v in b.items():
        if k in a:
            if policy == "skip":
                continue
            elif policy == "override":
                a[k] = v
            elif policy == "error":
                errors.append(f"Conflict in {what}: id '{k}' already exists")
        else:
            a[k] = v
    return list(a.values())


def load_base_bundle(data_root: Path) -> Dict[str, Any]:
    return {
        "abilities": (load_abilities(data_root / "abilities.yaml") or {}).get("abilities", []),
        "damage_types": (load_damage_types(data_root / "damage_types.yaml") or {}).get(
            "damage_types", []
        ),
        "narration": (load_narration(data_root / "narration.yaml") or {}),
        "body_parts": (load_body_parts(data_root / "body_parts.yaml") or {}),
        "status_effects": (load_status_effects(data_root / "status_effects.yaml") or {}),
    }


def load_pack_bundle(pack_dir: Path) -> Dict[str, Any]:
    # read yaml files if present
    out = {
        "abilities": [],
        "damage_types": [],
        "narration": {},
        "body_parts": {},
        "status_effects": {},
    }
    p = pack_dir
    if (p / "abilities.yaml").exists():
        out["abilities"] = (_read_yaml(p / "abilities.yaml") or {}).get("abilities", [])
    if (p / "damage_types.yaml").exists():
        out["damage_types"] = (_read_yaml(p / "damage_types.yaml") or {}).get("damage_types", [])
    if (p / "narration.yaml").exists():
        out["narration"] = _read_yaml(p / "narration.yaml") or {}
    if (p / "body_parts.yaml").exists():
        out["body_parts"] = _read_yaml(p / "body_parts.yaml") or {}
    if (p / "status_effects.yaml").exists():
        out["status_effects"] = _read_yaml(p / "status_effects.yaml") or {}
    return out


def load_content_packs_config(cfg_path: Path) -> Dict[str, Any]:
    if not cfg_path.exists():
        return {"enabled": [], "policy": "skip"}
    with open(cfg_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("enabled", [])
    data.setdefault("policy", "skip")
    return data


def merge_content_with_packs(data_root: Path) -> Tuple[Dict[str, Any], List[str]]:
    """
    Returns (bundle, errors). Bundle keys:
      abilities (list), damage_types (list), narration (dict), body_parts (dict), status_effects (dict)
    """
    errors: List[str] = []
    base = load_base_bundle(data_root)
    cfg = load_content_packs_config(data_root / "content_packs.yaml")
    policy = str(cfg.get("policy", "skip")).lower()
    enabled = cfg.get("enabled", []) or []

    merged = {
        "abilities": list(base["abilities"]),
        "damage_types": list(base["damage_types"]),
        "narration": dict(base["narration"]),
        "body_parts": dict(base["body_parts"]),
        "status_effects": dict(base["status_effects"]),
    }

    for pack in enabled:
        pd = data_root / "packs" / pack
        if not pd.exists():
            errors.append(f"Enabled pack '{pack}' not found at {pd}")
            continue
        bundle = load_pack_bundle(pd)
        merged["abilities"] = _merge_lists(
            merged["abilities"], bundle["abilities"], policy, "abilities", errors
        )
        merged["damage_types"] = _merge_lists(
            merged["damage_types"],
            bundle["damage_types"],
            policy,
            "damage_types",
            errors,
        )
        # narration/body_parts/status_effects are dicts → shallow-merge keys
        for k, v in (bundle.get("narration") or {}).items():
            if k not in merged["narration"]:
                merged["narration"][k] = v
            else:
                # naive merge for lists; override for scalars
                if isinstance(v, list) and isinstance(merged["narration"][k], list):
                    merged["narration"][k] = list({*merged["narration"][k], *v})
                else:
                    # "override" behavior for narration keys; policy doesn't apply here
                    merged["narration"][k] = v
        # body parts
        for k, v in (bundle.get("body_parts") or {}).items():
            if k not in merged["body_parts"]:
                merged["body_parts"][k] = v
            else:
                # groups/weights: override per-key
                if isinstance(v, dict) and isinstance(merged["body_parts"][k], dict):
                    merged["body_parts"][k].update(v)
                else:
                    merged["body_parts"][k] = v
        # status effects
        for k, v in (bundle.get("status_effects") or {}).items():
            if k not in merged["status_effects"]:
                merged["status_effects"][k] = v
            else:
                if policy == "skip":
                    continue
                elif policy == "override":
                    merged["status_effects"][k] = v
                elif policy == "error":
                    errors.append(f"Conflict in status_effects: id '{k}' already exists")
    return merged, errors
