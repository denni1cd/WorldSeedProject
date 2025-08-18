from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ...models.character import Character
from ...models.factory import create_new_character


@dataclass
class CreationSelections:
    name: str
    class_index: int
    trait_ids: List[str]
    race_index: int = 0


def _unwrap_list(wrapper_key: str, obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, dict) and wrapper_key in obj:
        vals = obj[wrapper_key]
        return list(vals) if isinstance(vals, list) else []
    if isinstance(obj, list):
        return list(obj)
    return []


def _unwrap_map(wrapper_key: str, obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict) and wrapper_key in obj:
        vals = obj[wrapper_key]
        return dict(vals) if isinstance(vals, dict) else {}
    if isinstance(obj, dict):
        return dict(obj)
    return {}


def list_starter_classes(class_catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    classes = _unwrap_list("classes", class_catalog)
    return [c for c in classes if not c.get("prereq")]


def list_traits(trait_catalog: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    traits = _unwrap_map("traits", trait_catalog)
    return sorted(traits.items(), key=lambda kv: kv[0])


def list_races(race_catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    return _unwrap_list("races", race_catalog)


def create_new_character_state(
    name: str,
    stat_tmpl: Dict[str, dict],
    slot_tmpl: Dict[str, dict],
    appearance_fields: Dict[str, dict],
    appearance_defaults: Dict[str, Any] | None,
    resources: Dict[str, Any],
) -> Character:
    return create_new_character(
        name,
        stat_tmpl,
        slot_tmpl,
        appearance_fields,
        appearance_defaults,
        resources,
    )


def apply_appearance_selection(hero: Character, selection: Dict[str, Any]) -> None:
    if not selection:
        return
    hero.appearance.update(selection)


def build_character_from_selections(
    sel: CreationSelections,
    stat_tmpl: Dict[str, dict],
    slot_tmpl: Dict[str, dict],
    appearance_fields: Dict[str, dict],
    appearance_defaults: Dict[str, Any],
    resources: Dict[str, Any],
    class_catalog: Dict[str, Any],
    trait_catalog: Dict[str, Any],
    race_catalog: Dict[str, Any],
) -> Character:
    # Unwrap fields if wrapped under 'fields'
    fields_spec = appearance_fields.get("fields", appearance_fields)
    hero = create_new_character_state(
        sel.name, stat_tmpl, slot_tmpl, fields_spec, appearance_defaults, resources
    )

    starters = list_starter_classes(class_catalog)
    if starters:
        idx = max(0, min(sel.class_index, len(starters) - 1))
        hero.classes = [starters[idx].get("id")]

    all_traits = _unwrap_map("traits", trait_catalog)
    hero.traits = [tid for tid in sel.trait_ids if tid in all_traits]

    races = list_races(race_catalog)
    if races:
        ridx = max(0, min(getattr(sel, "race_index", 0), len(races) - 1))
        hero.race = races[ridx].get("id")

    # Populate appearance with defaults if available
    fields = fields_spec
    for fid, meta in fields.items():
        if fid not in hero.appearance:
            if appearance_defaults and fid in appearance_defaults:
                hero.appearance[fid] = appearance_defaults[fid]
            elif "default" in meta:
                hero.appearance[fid] = meta["default"]

    return hero


def summarize_character(
    hero: Character,
    starters: List[Dict[str, Any]],
    class_index: int,
    trait_catalog: Dict[str, Any],
    race_catalog: Dict[str, Any],
) -> Dict[str, Any]:
    class_label = None
    if starters:
        idx = max(0, min(class_index, len(starters) - 1))
        class_label = starters[idx].get("name") or starters[idx].get("id")

    traits_map = _unwrap_map("traits", trait_catalog)
    trait_labels = []
    for tid in hero.traits:
        meta = traits_map.get(tid, {})
        trait_labels.append(meta.get("name", tid))

    race_label = None
    for r in list_races(race_catalog):
        if r.get("id") == hero.race:
            race_label = r.get("name", r.get("id"))
            break

    core_stats = {k: v for k, v in hero.stats.items() if isinstance(v, (int, float))}

    return {
        "name": hero.name,
        "class_label": class_label or "",
        "traits_labels": trait_labels,
        "hp": hero.hp,
        "mana": hero.mana,
        "core_stats": core_stats,
        "race_label": race_label or "",
        "appearance_peek": {k: hero.appearance.get(k) for k in list(hero.appearance.keys())[:5]},
    }
