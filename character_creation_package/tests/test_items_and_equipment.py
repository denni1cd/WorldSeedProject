import pytest
from character_creation.loaders.items_loader import load_item_catalog
from character_creation.loaders.stats_loader import load_stat_template
from character_creation.loaders.slots_loader import load_slot_template
from character_creation.loaders.appearance_loader import load_appearance_fields
from character_creation.loaders.resources_loader import load_resources
from character_creation.models import factory
from character_creation.services.equipment_logic import item_fits_slot, can_equip

import os


@pytest.fixture(scope="module")
def stat_tmpl():
    return load_stat_template(
        os.path.join(
            os.path.dirname(__file__), "..", "character_creation", "data", "stats", "stats.yaml"
        )
    )


@pytest.fixture(scope="module")
def slot_tmpl():
    return load_slot_template(
        os.path.join(os.path.dirname(__file__), "..", "character_creation", "data", "slots.yaml")
    )


@pytest.fixture(scope="module")
def appearance_fields():
    return load_appearance_fields(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "character_creation",
            "data",
            "appearance",
            "fields.yaml",
        )
    )


@pytest.fixture(scope="module")
def appearance_defaults():
    return None


@pytest.fixture(scope="module")
def resources():
    return load_resources(
        os.path.join(
            os.path.dirname(__file__), "..", "character_creation", "data", "resources.yaml"
        )
    )


@pytest.fixture(scope="module")
def item_catalog():
    return {
        item["id"]: item
        for item in load_item_catalog(
            os.path.join(
                os.path.dirname(__file__), "..", "character_creation", "data", "items.yaml"
            )
        )
    }


@pytest.fixture
def hero(stat_tmpl, slot_tmpl, appearance_fields, appearance_defaults, resources, item_catalog):
    return factory.create_new_character(
        "ItemHero",
        stat_tmpl,
        slot_tmpl,
        appearance_fields,
        appearance_defaults,
        resources,
        item_catalog,
    )


def test_items_loader_schema(item_catalog):
    assert item_catalog, "item_catalog should not be empty"
    for item_id, item in item_catalog.items():
        assert "id" in item
        assert "name" in item
        assert "slot" in item


def test_item_fits_slot_and_can_equip(hero, item_catalog, slot_tmpl):
    # Pick a weapon that fits a hand_main slot
    for item in item_catalog.values():
        if item.get("type") == "weapon":
            item_id = item["id"]
            slot_id = "hand_main"
            # Patch item slot for test to match slot_tmpl
            item["slot"] = slot_id
            # Patch stat keys to match hero.stats (uppercase)
            if "mods" in item and "stats" in item["mods"]:
                item["mods"]["stats"] = {k.upper(): v for k, v in item["mods"]["stats"].items()}
            assert item_fits_slot(item, slot_id, slot_tmpl)
            assert can_equip(hero, item_id, slot_id, item_catalog, slot_tmpl)
            break


def test_equip_applies_mods(hero, item_catalog):
    # Pick a weapon with stat mod and ability
    for item in item_catalog.values():
        if (
            item.get("type") == "weapon"
            and "stats" in item.get("mods", {})
            and item["mods"].get("abilities")
        ):
            item_id = item["id"]
            slot_id = "hand_main"
            # Patch item slot for test to match slot_tmpl
            item["slot"] = slot_id
            # Patch stat keys to match hero.stats (uppercase)
            item["mods"]["stats"] = {k.upper(): v for k, v in item["mods"]["stats"].items()}
            hero.add_to_inventory(item_id)
            hero.equip(item_id, slot_id, item_catalog)
            assert hero.equipment[slot_id] == item_id
            # Check for STR or similar stat mod
            for stat in item["mods"]["stats"]:
                assert hero.equipped_stat_mods.get(stat, 0) > 0
            # Check for ability
            for ab in item["mods"]["abilities"]:
                assert ab in hero.equipped_abilities
            old_stat = hero.get_effective_stat(list(item["mods"]["stats"].keys())[0])
            hero.unequip(slot_id, item_catalog)
            assert hero.get_effective_stat(list(item["mods"]["stats"].keys())[0]) < old_stat
            for ab in item["mods"]["abilities"]:
                assert ab not in hero.equipped_abilities
            break
