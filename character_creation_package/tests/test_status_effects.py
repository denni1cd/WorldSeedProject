import time
import pathlib
import yaml
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    status_effects_loader,
)
from character_creation.models.factory import create_new_character


def setup_character():
    root = pathlib.Path(__file__).parent.parent / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml")
    defaults = appearance_loader.load_appearance_defaults(root / "appearance" / "defaults.yaml")
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    effects = status_effects_loader.load_status_effects(root / "status_effects.yaml")
    formulas = yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))
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
    return hero, effects


def test_poison_tick_reduces_hp():
    hero, effects = setup_character()
    hero.hp = 10
    hero.apply_status_effect(
        "poison",
        effects["poison"],
        time.time() - effects["poison"]["tick_interval"],
    )
    hero.update_status_effects(time.time())
    assert hero.hp < 10


def test_expired_effect_removed():
    hero, effects = setup_character()
    hero.apply_status_effect(
        "bless",
        effects["bless"],
        time.time() - effects["bless"]["duration"] - 1,
    )
    hero.update_status_effects(time.time())
    assert len(hero.active_effects) == 0
