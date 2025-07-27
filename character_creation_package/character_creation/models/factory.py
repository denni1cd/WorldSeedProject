from typing import Dict, Any
from .character import Character


def create_new_character(
    name: str,
    stat_tmpl: Dict[str, dict],
    slot_tmpl: Dict[str, dict],
    appearance_fields: Dict[str, dict],
    appearance_defaults: Dict[str, Any] | None,
    resources: Dict[str, Any],
) -> Character:
    stats = {k: v["initial"] for k, v in stat_tmpl.items()}
    stat_xp = {k: 0.0 for k in stat_tmpl}
    hp = resources["baseline"]["hp"]
    mana = resources["baseline"]["mana"]
    hero = Character(name, stats, stat_xp, hp=hp, mana=mana)
    hero.init_equipment_slots(slot_tmpl)
    hero.init_appearance(appearance_fields, appearance_defaults)
    return hero
