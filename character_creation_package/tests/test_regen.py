import time
import pathlib
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    resources_config_loader,
)
from character_creation.models.factory import create_new_character


def setup_character():
    # Resolve absolute data directory like other tests
    root = pathlib.Path(__file__).parent.parent / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml")
    defaults = appearance_loader.load_appearance_defaults(root / "appearance" / "defaults.yaml")
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    resource_config = resources_config_loader.load_resource_config(root / "resources_config.yaml")
    formulas = __import__("yaml").safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))
    hero = create_new_character(
        "TestHero",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )
    return hero, resource_config


def test_hp_mana_regen():
    hero, rcfg = setup_character()
    hero.hp = 0
    hero.mana = 0
    now = time.time()
    hero.regen_tick(rcfg, now + rcfg["regen_intervals"]["hp"])
    assert hero.hp > 0 or hero.mana > 0
