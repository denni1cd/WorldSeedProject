from __future__ import annotations
from typing import Dict, Any, List


class ValidationError(Exception):
    pass


def _uniq_ids(seq: List[dict], label: str) -> List[str]:
    ids, seen = [], set()
    for item in seq or []:
        iid = item.get("id")
        if iid is None:
            ids.append(f"{label} item missing id")
            continue
        if iid in seen:
            ids.append(f"{label} id '{iid}' duplicated")
        seen.add(iid)
    return ids


def validate_damage_types(data: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    seq = (data or {}).get("damage_types", [])
    errs += _uniq_ids(seq, "damage_types")
    for dt in seq:
        if "id" not in dt or not isinstance(dt["id"], str):
            errs.append("damage_types requires string id")
        if "label" in dt and not isinstance(dt["label"], str):
            errs.append(f"damage_types '{dt.get('id','?')}' label must be string")
    return errs


def validate_abilities(data: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    seq = (data or {}).get("abilities", [])
    errs += _uniq_ids(seq, "abilities")
    for ab in seq:
        if not isinstance(ab.get("id"), str):
            errs.append("ability missing string id")
        if not isinstance(ab.get("name", ""), str):
            errs.append(f"ability {ab.get('id','?')} missing name")
        if not isinstance(ab.get("formula", ""), str):
            errs.append(f"ability {ab.get('id','?')} missing formula")
        if not isinstance(ab.get("damage_type", ""), str):
            errs.append(f"ability {ab.get('id','?')} missing damage_type")
        if "cooldown" in ab and not isinstance(ab["cooldown"], (int, float)):
            errs.append(f"ability {ab.get('id','?')} cooldown must be number")
        if "resource_cost" in ab and not isinstance(ab["resource_cost"], dict):
            errs.append(f"ability {ab.get('id','?')} resource_cost must be mapping")
    return errs


def validate_status_effects(data: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    effs = (data or {}).get("effects", {})
    if not isinstance(effs, dict):
        return ["status_effects.effects must be mapping"]
    for eid, ed in effs.items():
        if not isinstance(eid, str):
            errs.append("status_effect id must be string")
        if not isinstance(ed, dict):
            errs.append(f"status_effect {eid} must be mapping")
        if "duration" in ed and not isinstance(ed["duration"], int):
            errs.append(f"status_effect {eid} duration must be int")
        if "per_tick" in ed and not isinstance(ed["per_tick"], str):
            errs.append(f"status_effect {eid} per_tick must be string expression")
        if "max_stacks" in ed and not isinstance(ed["max_stacks"], int):
            errs.append(f"status_effect {eid} max_stacks must be int")
    return errs


def validate_body_parts(data: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    groups = (data or {}).get("groups", {})
    weights = (data or {}).get("weights", {})
    if not isinstance(groups, dict):
        errs.append("body_parts.groups must be mapping")
    if not isinstance(weights, dict):
        errs.append("body_parts.weights must be mapping")
    for g, parts in (groups or {}).items():
        if not isinstance(parts, list) or not all(isinstance(x, str) for x in parts):
            errs.append(f"body_parts.groups.{g} must be list[str]")
    # optional: ensure weight keys exist in group
    for g, wmap in (weights or {}).items():
        if not isinstance(wmap, dict):
            errs.append(f"body_parts.weights.{g} must be mapping")
        else:
            for k in wmap.keys():
                if k not in (groups.get(g) or []):
                    errs.append(f"body_parts.weights.{g}.{k} not in groups.{g}")
    return errs


def validate_narration(data: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if data is None:
        return errs
    if "templates" in data and not isinstance(data["templates"], dict):
        errs.append("narration.templates must be mapping")
    # optional deep checks could be added here
    return errs


def cross_validate(bundle: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    dmg_ids = {
        d.get("id") for d in (bundle.get("damage_types") or []) if isinstance(d.get("id"), str)
    }
    effects = (bundle.get("status_effects") or {}).get("effects", {})
    effect_ids = set(effects.keys())
    # abilities → damage_type + on_hit effect ids
    for ab in bundle.get("abilities") or []:
        dt = ab.get("damage_type")
        if isinstance(dt, str) and dt not in dmg_ids:
            errs.append(f"ability '{ab.get('id')}' references unknown damage_type '{dt}'")
        oh = (ab.get("on_hit") or {}).get("apply_status") or []
        for spec in oh:
            eid = spec.get("id")
            if eid and eid not in effect_ids:
                errs.append(f"ability '{ab.get('id')}' on_hit references unknown status '{eid}'")
    # effects → damage types
    for eid, ed in effects.items():
        dt = ed.get("damage_type")
        if isinstance(dt, str) and dt not in dmg_ids:
            errs.append(f"status_effect '{eid}' references unknown damage_type '{dt}'")
    return errs
