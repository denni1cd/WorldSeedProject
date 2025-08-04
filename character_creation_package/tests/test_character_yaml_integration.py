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

# 1) Test that abilities from grants_abilities are added to the hero


def test_class_abilities_from_yaml():
    class_catalog = classes_loader.load_class_catalog(Path("character_creation/data/classes.yaml"))
    # If class_catalog is a dict, get first value; if list, get first item
    # If the YAML root is a dict with 'classes', use that list
    if isinstance(class_catalog, dict) and "classes" in class_catalog:
        class_list = class_catalog["classes"]
        class_entry = class_list[0]
    elif isinstance(class_catalog, list):
        class_entry = class_catalog[0]
    else:
        raise TypeError("class_catalog is not a dict with 'classes' or a list")
    hero = factory.create_new_character(
        name="TestHero",
        stat_tmpl=stats_loader.load_stat_template(Path("character_creation/data/stats/stats.yaml")),
        slot_tmpl=slots_loader.load_slot_template(Path("character_creation/data/slots.yaml")),
        appearance_fields=appearance_loader.load_appearance_fields(
            Path("character_creation/data/appearance/fields.yaml")
        ),
        appearance_defaults=appearance_loader.load_appearance_defaults(
            Path("character_creation/data/appearance/defaults.yaml")
        ),
        resources=resources_loader.load_resources(Path("character_creation/data/resources.yaml")),
    )
    hero.add_class(class_entry)
    expected_abilities = class_entry.get("grants_abilities", [])
    for ab in expected_abilities:
        assert ab in hero.abilities


# 2) Test the full run_wizard flow


def test_run_wizard_full_flow(monkeypatch, tmp_path):
    # Prepare loaders_dict
    loaders_dict = {
        "stat_tmpl": stats_loader.load_stat_template(
            Path("character_creation/data/stats/stats.yaml")
        ),
        "slot_tmpl": slots_loader.load_slot_template(Path("character_creation/data/slots.yaml")),
        "appearance_fields": appearance_loader.load_appearance_fields(
            Path("character_creation/data/appearance/fields.yaml")
        ),
        "appearance_defaults": appearance_loader.load_appearance_defaults(
            Path("character_creation/data/appearance/defaults.yaml")
        ),
        "resources": resources_loader.load_resources(
            Path("character_creation/data/resources.yaml")
        ),
        "classes_loader": classes_loader.load_class_catalog(
            Path("character_creation/data/classes.yaml")
        ),
        "traits_loader": traits_loader.load_trait_catalog(
            Path("character_creation/data/traits.yaml")
        ),
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
