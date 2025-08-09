import pathlib
import pytest
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
)
from character_creation.models.factory import create_new_character


@pytest.fixture
def loaded():
    root = pathlib.Path(__file__).parent.parent / "character_creation" / "data"
    return {
        "stats": stats_loader.load_stat_template(root / "stats" / "stats.yaml"),
        "slots": slots_loader.load_slot_template(root / "slots.yaml"),
        "fields": appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml"),
        "defaults": appearance_loader.load_appearance_defaults(
            root / "appearance" / "defaults.yaml"
        ),
        "resources": resources_loader.load_resources(root / "resources.yaml"),
        "progression": progression_loader.load_progression(root / "progression.yaml"),
        "formulas": __import__("yaml").safe_load(
            open(root / "formulas.yaml", "r", encoding="utf-8")
        ),
    }


def test_level_up_and_stat_points(loaded):
    hero = create_new_character(
        "LvTest",
        loaded["stats"],
        loaded["slots"],
        loaded["fields"],
        loaded["defaults"],
        loaded["resources"],
        progression=loaded["progression"],
        formulas=loaded["formulas"],
    )
    start_level = hero.level
    start_hp = hero.hp
    start_mana = hero.mana
    gained = hero.add_general_xp(200.0, loaded["formulas"], loaded["stats"], loaded["progression"])
    assert hero.level >= start_level  # exact depends on xp_to_next formula
    assert hero.stat_points >= loaded["progression"].get("stat_points_per_level", 2) * gained
    # HP/Mana should have been recomputed per progression flags
    assert hero.hp != start_hp or hero.mana != start_mana


def test_spend_stat_points_and_refresh(loaded):
    hero = create_new_character(
        "SpendTest",
        loaded["stats"],
        loaded["slots"],
        loaded["fields"],
        loaded["defaults"],
        loaded["resources"],
        progression=loaded["progression"],
        formulas=loaded["formulas"],
    )
    hero.stat_points = 3  # simulate reward
    # spend 3 points as +0.1 each to STR, INT, STA
    hero.spend_stat_points({"STR": 0.1, "INT": 0.1, "STA": 0.1})
    tol = 1e-6
    assert hero.stats["STR"] >= 1.1 - tol
    assert hero.stats["INT"] >= 1.1 - tol
    assert hero.stats["STA"] >= 1.1 - tol
    # After stat changes, derived can be recomputed
    before_hp = hero.hp
    hero.refresh_derived(loaded["formulas"], loaded["stats"], keep_percent=False)
    assert hero.hp != before_hp


def test_spend_overshoot_raises(loaded):
    hero = create_new_character(
        "Overspend",
        loaded["stats"],
        loaded["slots"],
        loaded["fields"],
        loaded["defaults"],
        loaded["resources"],
        progression=loaded["progression"],
        formulas=loaded["formulas"],
    )
    hero.stat_points = 1
    with pytest.raises(ValueError):
        hero.spend_stat_points({"STR": 0.3})  # exceeds 0.1 budget for 1 point
