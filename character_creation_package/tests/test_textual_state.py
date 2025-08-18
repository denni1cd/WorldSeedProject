import pytest
from pathlib import Path

from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    races_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from character_creation.ui.textual import state


DATA_ROOT = (
    Path(__file__).parents[2]
    / "character_creation_package"
    / "character_creation"
    / "data"
)


@pytest.fixture(scope="module")
def loaded_data():
    return {
        "stat_tmpl": stats_loader.load_stat_template(
            DATA_ROOT / "stats" / "stats.yaml"
        ),
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


def test_list_starter_classes_and_traits(loaded_data):
    starters = state.list_starter_classes(loaded_data["class_catalog"])
    assert isinstance(starters, list) and len(starters) >= 1
    for cls in starters:
        assert not cls.get("prereq")

    traits = state.list_traits(loaded_data["trait_catalog"])
    assert isinstance(traits, list) and len(traits) >= 1
    # Sorted by id ascending
    ids = [tid for tid, _ in traits]
    assert ids == sorted(ids)


def test_build_and_summarize_character(loaded_data):
    traits = state.list_traits(loaded_data["trait_catalog"])
    first_trait_id = traits[0][0]

    sel = state.CreationSelections(
        name="TuiHero", class_index=0, trait_ids=[first_trait_id]
    )
    hero = state.build_character_from_selections(
        sel,
        loaded_data["stat_tmpl"],
        loaded_data["slot_tmpl"],
        loaded_data["appearance_fields"],
        loaded_data["appearance_defaults"],
        loaded_data["resources"],
        loaded_data["class_catalog"],
        loaded_data["trait_catalog"],
        loaded_data["race_catalog"],
    )

    # Basic assertions
    assert hero.name == "TuiHero"
    assert getattr(hero, "classes", None)
    assert first_trait_id in getattr(hero, "traits", [])

    # Equipment initialized for all slots
    slot_keys = list(
        loaded_data["slot_tmpl"].get("slots", loaded_data["slot_tmpl"]).keys()
    )
    for key in slot_keys:
        assert key in hero.equipment

    # Appearance keys match field spec
    field_spec = loaded_data["appearance_fields"].get(
        "fields", loaded_data["appearance_fields"]
    )
    assert set(hero.appearance.keys()) == set(field_spec.keys())

    # Summary
    starters = state.list_starter_classes(loaded_data["class_catalog"])
    summary = state.summarize_character(
        hero,
        starters,
        sel.class_index,
        loaded_data["trait_catalog"],
        loaded_data["race_catalog"],
    )
    for k in ["name", "class_label", "traits_labels", "hp", "mana", "core_stats"]:
        assert k in summary
    assert summary["name"] == "TuiHero"
    assert isinstance(summary["class_label"], str) and summary["class_label"]
    assert isinstance(summary["traits_labels"], list)
    assert isinstance(summary["hp"], (int, float))
    assert isinstance(summary["mana"], (int, float))
    assert isinstance(summary["core_stats"], dict) and summary["core_stats"]
    # Races list non-empty and summary includes race_label key
    races = state.list_races(loaded_data["race_catalog"])
    assert isinstance(races, list) and len(races) >= 1
    assert "race_label" in summary
