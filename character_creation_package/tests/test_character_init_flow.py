import pytest
from character_creation.models.factory import create_new_character
from character_creation import Character
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)


@pytest.fixture(scope="module")
def stat_tmpl():
    # Use the correct function and path for loading stats
    from pathlib import Path

    stats_path = (
        Path(__file__).parent.parent / "character_creation" / "data" / "stats" / "stats.yaml"
    )
    return stats_loader.load_stat_template(stats_path)


@pytest.fixture(scope="module")
def slot_tmpl():
    # Use the correct function and path for loading slots
    from pathlib import Path

    slots_path = Path(__file__).parent.parent / "character_creation" / "data" / "slots.yaml"
    return slots_loader.load_slot_template(slots_path)


@pytest.fixture(scope="module")
def appearance_fields():
    return appearance_loader.load_fields()


@pytest.fixture(scope="module")
def appearance_defaults():
    try:
        return appearance_loader.load_defaults()
    except Exception:
        return {}


@pytest.fixture(scope="module")
def resources():
    return resources_loader.load_resources_default()


def test_character_init_flow(
    tmp_path, stat_tmpl, slot_tmpl, appearance_fields, appearance_defaults, resources
):
    hero = create_new_character(
        "TestHero",
        stat_tmpl,
        slot_tmpl,
        appearance_fields,
        appearance_defaults,
        resources,
    )
    # Assert stats
    for k, v in stat_tmpl.items():
        assert hero.stats[k] == v["initial"]
    # Assert hp/mana
    assert hero.hp == resources["baseline"]["hp"]
    assert hero.mana == resources["baseline"]["mana"]
    # Assert equipment slots
    for slot in slot_tmpl["slots"]:
        assert slot in hero.equipment
        assert hero.equipment[slot] is None
    # Assert appearance fields
    for field_id, meta in appearance_fields.items():
        expected = (
            appearance_defaults.get(field_id, meta.get("default"))
            if appearance_defaults
            else meta.get("default")
        )
        assert hero.appearance[field_id] == expected
    # Save/load
    json_path = tmp_path / "hero.json"
    hero.to_json(json_path)
    hero2 = Character.from_json(json_path)
    assert hero2.name == hero.name
    assert hero2.stats == hero.stats
    assert hero2.hp == hero.hp
    assert hero2.mana == hero.mana
    assert hero2.equipment == hero.equipment
    assert hero2.appearance == hero.appearance
