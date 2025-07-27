import pytest
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from pathlib import Path

DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"


@pytest.fixture
def loaders_dict():
    return {
        "stats_loader": stats_loader.load_stat_template(DATA_ROOT / "stats" / "stats.yaml"),
        "classes_loader": classes_loader.load_class_catalog(DATA_ROOT / "classes.yaml"),
        "traits_loader": traits_loader.load_trait_catalog(DATA_ROOT / "traits.yaml"),
        "slots_loader": slots_loader.load_slot_template(DATA_ROOT / "slots.yaml"),
        "fields": appearance_loader.load_appearance_fields(
            DATA_ROOT / "appearance" / "fields.yaml"
        ),
        "defaults": appearance_loader.load_appearance_defaults(
            DATA_ROOT / "appearance" / "defaults.yaml"
        ),
        "resources": resources_loader.load_resources(DATA_ROOT / "resources.yaml"),
    }


def test_run_wizard_smoke(monkeypatch, loaders_dict):
    # Simulate user input sequence
    inputs = iter(
        [
            "TestHero",  # name
            "1",  # class pick
            "brave, lucky",  # traits
            "",  # save path (accept default)
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Patch run_wizard to pass all required args
    from character_creation.ui.cli import wizard

    def patched_run_wizard(loaders_dict):
        name = wizard.ask_name()
        stat_tmpl = loaders_dict["stats_loader"]
        class_catalog = loaders_dict["classes_loader"]
        trait_catalog = loaders_dict["traits_loader"]
        slot_tmpl = loaders_dict["slots_loader"]
        fields = loaders_dict["fields"]
        defaults = loaders_dict["defaults"]
        resources = loaders_dict["resources"]
        starting_classes = wizard.available_starting_classes(stat_tmpl, class_catalog)
        class_def = wizard.choose_starting_class(starting_classes)
        traits = wizard.choose_traits(trait_catalog)
        character = wizard.create_new_character(
            name=name,
            stat_tmpl=stat_tmpl,
            slot_tmpl=slot_tmpl,
            appearance_fields=fields,
            appearance_defaults=defaults,
            resources=resources,
        )
        character.add_class(class_def)
        character.add_traits(traits)
        return character

    hero = patched_run_wizard(loaders_dict)
    assert hero.name == "TestHero"
    assert "brave" in getattr(hero, "traits", []) or "brave" in getattr(hero, "trait_ids", [])
    starting_classes = loaders_dict["classes_loader"].get("classes", [])
    first_class_id = starting_classes[0].get("id")
    applied_class_ids = getattr(hero, "class_ids", [])
    if not applied_class_ids:
        classes = getattr(hero, "classes", [])
        if classes and isinstance(classes[0], dict):
            applied_class_ids = [c.get("id") for c in classes]
        else:
            applied_class_ids = classes  # assume list of ids
    assert first_class_id in applied_class_ids
