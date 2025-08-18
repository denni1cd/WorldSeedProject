import os
import pytest

from character_creation.loaders.stats_loader import load_stat_template
from character_creation.loaders.slots_loader import load_slot_template
from character_creation.loaders.appearance_loader import load_appearance_fields
from character_creation.loaders.resources_loader import load_resources
from character_creation.loaders.items_loader import load_item_catalog
from character_creation.models import factory


@pytest.fixture(scope="module")
def data_dir():
    return os.path.join(os.path.dirname(__file__), "..", "character_creation", "data")


@pytest.fixture(scope="module")
def stat_tmpl(data_dir):
    return load_stat_template(os.path.join(data_dir, "stats", "stats.yaml"))


@pytest.fixture(scope="module")
def slot_tmpl(data_dir):
    return load_slot_template(os.path.join(data_dir, "slots.yaml"))


@pytest.fixture(scope="module")
def appearance_fields(data_dir):
    return load_appearance_fields(os.path.join(data_dir, "appearance", "fields.yaml"))


@pytest.fixture(scope="module")
def appearance_defaults():
    return None


@pytest.fixture(scope="module")
def resources(data_dir):
    return load_resources(os.path.join(data_dir, "resources.yaml"))


@pytest.fixture(scope="module")
def items_catalog(data_dir):
    return {
        item["id"]: item
        for item in load_item_catalog(os.path.join(data_dir, "items.yaml"))
    }


@pytest.fixture
def hero(
    stat_tmpl,
    slot_tmpl,
    appearance_fields,
    appearance_defaults,
    resources,
    items_catalog,
):
    return factory.create_new_character(
        "InvHero",
        stat_tmpl,
        slot_tmpl,
        appearance_fields,
        appearance_defaults,
        resources,
        items_catalog,
    )


def test_inventory_not_duplicated_on_equip_unequip(hero, items_catalog):
    # Ensure iron_sword exists in catalog; if not, skip
    if "iron_sword" not in items_catalog:
        pytest.skip("iron_sword not in catalog")

    hero.add_to_inventory("iron_sword")
    count_before = hero.inventory.count("iron_sword")

    # Equip to hand_main
    hero.equip("iron_sword", "hand_main", items_catalog)
    assert hero.inventory.count("iron_sword") == max(0, count_before - 1)

    # Unequip should add back once
    hero.unequip("hand_main", items_catalog)
    assert hero.inventory.count("iron_sword") == 1


def test_equip_not_in_inventory_then_unequip_adds_once(hero, items_catalog):
    # Ensure silver_ring exists in catalog; if not, skip
    if "silver_ring" not in items_catalog:
        pytest.skip("silver_ring not in catalog")

    # Make sure it's not in inventory initially
    hero.inventory = [i for i in hero.inventory if i != "silver_ring"]

    # Equip to accessory_1 (fits by category 'accessory')
    hero.equip("silver_ring", "accessory_1", items_catalog)

    # Unequip should add exactly once
    hero.unequip("accessory_1", items_catalog)
    assert hero.inventory.count("silver_ring") == 1
