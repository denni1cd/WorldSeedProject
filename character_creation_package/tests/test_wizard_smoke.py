import pytest
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    races_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from pathlib import Path

DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"


@pytest.fixture
def loaders_dict():
    return {
        "stat_tmpl": stats_loader.load_stat_template(DATA_ROOT / "stats" / "stats.yaml"),
        "class_catalog": classes_loader.load_class_catalog(DATA_ROOT / "classes.yaml"),
        "trait_catalog": traits_loader.load_trait_catalog(DATA_ROOT / "traits.yaml"),
        "race_catalog": races_loader.load_race_catalog(DATA_ROOT / "races.yaml"),
        "slot_tmpl": slots_loader.load_slot_template(DATA_ROOT / "slots.yaml"),
        "appearance_fields": appearance_loader.load_appearance_fields(
            DATA_ROOT / "appearance" / "fields.yaml"
        ),
        "appearance_defaults": appearance_loader.load_appearance_defaults(
            DATA_ROOT / "appearance" / "defaults.yaml"
        ),
        "resources": resources_loader.load_resources(DATA_ROOT / "resources.yaml"),
    }


def test_run_wizard_smoke(monkeypatch, loaders_dict):
    # Simulate user input sequence
    inputs = iter(
        [
            "TestHero",  # name
            "1",  # race pick (first race)
            "1",  # class pick
            "brave, lucky",  # traits
            "",  # save path (accept default)
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    from character_creation.ui.cli.wizard import run_wizard

    hero = run_wizard(loaders_dict)
    assert hero.name == "TestHero"
    assert getattr(hero, "race", None) is not None
    # Label resolution via catalog
    first_race = loaders_dict["race_catalog"].get("races", [])[0]
    assert first_race["id"] == hero.race
    assert "brave" in getattr(hero, "traits", [])
    starting_classes = loaders_dict["class_catalog"].get("classes", [])
    first_class_id = starting_classes[0].get("id")
    assert first_class_id in getattr(hero, "classes", [])

    # If trait data includes grants, ensure they took effect where possible
    brave_def = loaders_dict["trait_catalog"].get("traits", {}).get("brave", {})
    grants_stats = brave_def.get("grants_stats", {})
    for stat_key in grants_stats.keys():
        assert hero.stats.get(stat_key, 0) >= grants_stats[stat_key]
    for ability in brave_def.get("grants_abilities", []):
        assert ability in hero.abilities
