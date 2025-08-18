from pathlib import Path

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    races_loader,
)
from character_creation.models.factory import create_new_character


DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"
CHAR = DATA_ROOT / "character"
BACK = DATA_ROOT / "backend"


def pick(*candidates: Path) -> Path:
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            continue
    return candidates[-1]


def test_set_race_applies_effects():
    stat_tmpl = stats_loader.load_stat_template(
        pick(CHAR / "stats" / "stats.yaml", DATA_ROOT / "stats" / "stats.yaml")
    )
    slot_tmpl = slots_loader.load_slot_template(pick(BACK / "slots.yaml", DATA_ROOT / "slots.yaml"))
    fields = appearance_loader.load_appearance_fields(
        pick(CHAR / "appearance" / "fields.yaml", DATA_ROOT / "appearance" / "fields.yaml")
    )
    defaults = appearance_loader.load_appearance_defaults(
        pick(CHAR / "appearance" / "defaults.yaml", DATA_ROOT / "appearance" / "defaults.yaml")
    )
    resources = resources_loader.load_resources(
        pick(BACK / "resources.yaml", DATA_ROOT / "resources.yaml")
    )
    race_catalog = races_loader.load_race_catalog(
        pick(CHAR / "races.yaml", DATA_ROOT / "races.yaml")
    )

    hero = create_new_character("RaceHero", stat_tmpl, slot_tmpl, fields, defaults, resources)
    base_dex = hero.stats.get("DEX", 0)
    base_int = hero.stats.get("INT", 0)

    hero.set_race("elf", race_catalog)
    assert hero.race == "elf"
    assert hero.stats.get("DEX", 0) >= base_dex + 0.2 - 1e-9
    assert hero.stats.get("INT", 0) >= base_int + 0.1 - 1e-9
    assert "keen_senses" in hero.abilities
