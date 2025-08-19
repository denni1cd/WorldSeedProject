import pytest
from character_creation import Character
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)


@pytest.fixture(scope="module")
def stat_tmpl():
    from pathlib import Path

    stats_path = (
        Path(__file__).parent.parent
        / "character_creation"
        / "data"
        / "stats"
        / "stats.yaml"
    )
    return stats_loader.load_stat_template(stats_path)


@pytest.fixture(scope="module")
def slot_tmpl():
    from pathlib import Path

    slots_path = (
        Path(__file__).parent.parent / "character_creation" / "data" / "slots.yaml"
    )
    return slots_loader.load_slot_template(slots_path)


@pytest.fixture(scope="module")
def appearance_fields():
    return appearance_loader.load_fields()


@pytest.fixture(scope="module")
def appearance_defaults():
    return appearance_loader.load_defaults()


@pytest.fixture(scope="module")
def resources():
    return resources_loader.load_resources()


@pytest.fixture
def blank_hero():
    return Character(
        name="TestHero",
        stats={},
        stat_xp={},
        hp=20.0,
        mana=20.0,
        classes=[],
        abilities=set(),
        traits=[],
        inventory=[],
        equipment={},
        appearance={},
    )


def test_gain_xp_rollover(blank_hero, stat_tmpl):
    blank_hero.stats = {"STR": 1.0}
    blank_hero.stat_xp = {"STR": 0.0}
    blank_hero.gain_xp("STR", 120.0, stat_tmpl)
    assert pytest.approx(blank_hero.stats["STR"], 0.01) == 1.1
    assert pytest.approx(blank_hero.stat_xp["STR"], 0.01) == 20.0


def test_add_class(blank_hero):
    blank_hero.stats = {"STR": 1.0}
    fighter_def = {
        "id": "fighter",
        "grants_stats": {"STR": 1.0},
        "abilities": ["Power Strike"],
    }
    blank_hero.add_class(fighter_def)
    assert "fighter" in blank_hero.classes
    assert blank_hero.stats["STR"] == 2.0
    assert "Power Strike" in blank_hero.abilities


def test_traits_no_duplicates(blank_hero):
    blank_hero.traits = []
    blank_hero.add_traits(["brave", "brave"])
    assert blank_hero.traits == ["brave"]


def test_equipment_cycle(blank_hero, slot_tmpl):
    blank_hero.init_equipment_slots(slot_tmpl)
    blank_hero.add_to_inventory("iron_sword")
    # Dummy items_catalog for test
    items_catalog = {
        "iron_sword": {"id": "iron_sword", "slot": "hand_main", "mods": {}}
    }
    blank_hero.equip("iron_sword", "hand_main", items_catalog)
    assert blank_hero.equipment["hand_main"] == "iron_sword"
    blank_hero.unequip("hand_main", items_catalog)
    assert "iron_sword" in blank_hero.inventory
    assert blank_hero.equipment["hand_main"] is None
