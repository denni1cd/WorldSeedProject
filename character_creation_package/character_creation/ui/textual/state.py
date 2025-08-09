from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from ...models.factory import create_new_character


@dataclass
class CreationSelections:
    name: str
    class_index: int
    trait_ids: List[str]


def list_starter_classes(class_catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return classes with no prereq, preserving order."""

    classes: List[Dict[str, Any]] = list(class_catalog.get("classes", []))
    return [cls for cls in classes if not cls.get("prereq")]


def list_traits(trait_catalog: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Return list of (id, meta) sorted by id."""

    traits: Dict[str, Dict[str, Any]] = trait_catalog.get("traits", {})
    return sorted(traits.items(), key=lambda kv: kv[0])


def build_character_from_selections(
    sel: CreationSelections,
    stat_tmpl: Dict[str, Any],
    slot_tmpl: Dict[str, Any],
    appearance_fields: Dict[str, Any],
    appearance_defaults: Dict[str, Any],
    resources: Dict[str, Any],
    class_catalog: Dict[str, Any],
    trait_catalog: Dict[str, Any],
) -> Any:
    """
    - Create base hero via create_new_character
    - Apply chosen class (use starter list index)
    - Apply selected trait ids
    - Return hero
    """

    # Normalize possible nested schemas
    fields_spec = appearance_fields.get("fields", appearance_fields)
    hero = create_new_character(
        sel.name,
        stat_tmpl,
        slot_tmpl,
        fields_spec,
        appearance_defaults,
        resources,
    )

    starters = list_starter_classes(class_catalog)
    if not (0 <= sel.class_index < len(starters)):
        raise IndexError("class_index out of range for starter classes")
    chosen_class_def = starters[sel.class_index]
    hero.add_class(chosen_class_def)

    # Validate trait ids against catalog and apply
    valid_trait_ids = [tid for tid in sel.trait_ids if tid in trait_catalog.get("traits", {})]
    hero.add_traits(valid_trait_ids)

    return hero


def summarize_character(
    hero: Any,
    starter_classes: List[Dict[str, Any]],
    chosen_index: int,
    trait_catalog: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return dict with keys: name, class_label, traits_labels, hp, mana, core_stats (dict).
    Use 'name' field on class/trait if present, else the id.
    """

    class_label = None
    if 0 <= chosen_index < len(starter_classes):
        class_def = starter_classes[chosen_index]
        class_label = class_def.get("name") or class_def.get("id")

    trait_meta = trait_catalog.get("traits", {})
    traits_labels: List[str] = []
    for tid in getattr(hero, "traits", []) or []:
        meta = trait_meta.get(tid, {})
        traits_labels.append(meta.get("name") or tid)

    return {
        "name": getattr(hero, "name", None),
        "class_label": class_label,
        "traits_labels": traits_labels,
        "hp": getattr(hero, "hp", None),
        "mana": getattr(hero, "mana", None),
        "core_stats": getattr(hero, "stats", {}),
    }
