# character_creation_package/tests/test_character_yaml_integration.py

from pathlib import Path
from character_creation.loaders import (
    classes_loader,
    stats_loader,
    traits_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from character_creation.models import factory
from character_creation.ui.cli import wizard
import builtins
import json


def _data_dir() -> Path:
    """
    Resolve the absolute path to character_creation/data regardless of where pytest is run from.
    tests/.. -> character_creation_package, then /character_creation/data
    """
    return Path(__file__).parent.parent / "character_creation" / "data"


# 1) Test that abilities from grants_abilities are added to the hero
def test_class_abilities_from_yaml():
    DATA_DIR = _data_dir()
    class_catalog = classes_loader.load_class_catalog(DATA_DIR / "classes.yaml")

    # If class_catalog is a dict, get first value under 'classes'; if list, take first item
    if isinstance(class_catalog, dict) and "classes" in class_catalog:
        class_list = class_catalog["classes"]
        class_entry = class_list[0]
    elif isinstance(class_catalog, list):
        class_entry = class_catalog[0]
    else:
        raise TypeError("class_catalog is not a dict with 'classes' or a list")

    hero = factory.create_new_character(
        name="TestHero",
        stat_tmpl=stats_loader.load_stat_template(DATA_DIR / "stats" / "stats.yaml"),
        slot_tmpl=slots_loader.load_slot_template(DATA_DIR / "slots.yaml"),
        appearance_fields=appearance_loader.load_appearance_fields(
            DATA_DIR / "appearance" / "fields.yaml"
        ),
        appearance_defaults=appearance_loader.load_appearance_defaults(
            DATA_DIR / "appearance" / "defaults.yaml"
        ),
        resources=resources_loader.load_resources(DATA_DIR / "resources.yaml"),
    )

    hero.add_class(class_entry)

    expected_abilities = class_entry.get("grants_abilities", [])
    for ab in expected_abilities:
        assert ab in hero.abilities


# 2) Test the full run_wizard flow
def test_run_wizard_full_flow(monkeypatch, tmp_path):
    DATA_DIR = _data_dir()

    loaders_dict = {
        "stat_tmpl": stats_loader.load_stat_template(DATA_DIR / "stats" / "stats.yaml"),
        "slot_tmpl": slots_loader.load_slot_template(DATA_DIR / "slots.yaml"),
        "appearance_fields": appearance_loader.load_appearance_fields(
            DATA_DIR / "appearance" / "fields.yaml"
        ),
        "appearance_defaults": appearance_loader.load_appearance_defaults(
            DATA_DIR / "appearance" / "defaults.yaml"
        ),
        "resources": resources_loader.load_resources(DATA_DIR / "resources.yaml"),
        "classes_loader": classes_loader.load_class_catalog(DATA_DIR / "classes.yaml"),
        "traits_loader": traits_loader.load_trait_catalog(DATA_DIR / "traits.yaml"),
    }

    inputs = iter(["HeroName", "1", "brave, lucky", ""])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    monkeypatch.setattr(
        wizard, "confirm_save_path", lambda default_path: str(tmp_path / "hero.json")
    )

    hero = wizard.run_wizard(loaders_dict)

    assert hero.name == "HeroName"
    assert "brave" in hero.traits
    assert hero.classes

    hero.to_json(tmp_path / "hero.json")
    with open(tmp_path / "hero.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == "HeroName"
