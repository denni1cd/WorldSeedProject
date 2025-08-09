from typing import Dict, Any
from .character import Character


def create_new_character(
    name: str,
    stat_tmpl: Dict[str, dict],
    slot_tmpl: Dict[str, dict],
    appearance_fields: Dict[str, dict],
    appearance_defaults: Dict[str, Any] | None,
    resources: Dict[str, Any],
    items_catalog: Dict[str, Any] | None = None,
    progression: Dict[str, Any] | None = None,
    formulas: Dict[str, Any] | None = None,
) -> Character:
    stats = {k: v["initial"] for k, v in stat_tmpl.items()}
    stat_xp = {k: 0.0 for k in stat_tmpl}
    hp = resources["baseline"]["hp"]
    mana = resources["baseline"]["mana"]
    hero = Character(name, stats, stat_xp, hp=hp, mana=mana)
    # Initialize progression fields
    progression = progression or {}
    formulas = formulas or {}
    hero.level = int(progression.get("starting_level", 1))
    hero.xp_total = float(progression.get("starting_xp", 0))
    hero.stat_points = 0
    hero.init_equipment_slots(slot_tmpl)
    hero.init_appearance(appearance_fields, appearance_defaults)
    # Refresh derived resources from formulas if available
    try:
        baseline = formulas.get("baseline") if isinstance(formulas, dict) else None
        if baseline and "hp" in baseline and "mana" in baseline:
            hero.refresh_derived(formulas, stat_tmpl, keep_percent=False)
    except Exception:
        # Be tolerant if formulas are incomplete during initialization
        pass
    # items_catalog is ignored for now
    return hero
