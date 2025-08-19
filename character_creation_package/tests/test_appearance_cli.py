import builtins
from pathlib import Path

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


DATA_ROOT = (
    Path(__file__).parents[2]
    / "character_creation_package"
    / "character_creation"
    / "data"
)


@pytest.fixture
def loaders_dict():
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


def test_cli_choose_appearance_flow(monkeypatch, loaders_dict):
    # Prepare some concrete expectations using known YAML
    # eye_color enum first value and a numeric within range for height_cm
    from character_creation.ui.cli.wizard import run_wizard

    # Determine numeric bounds for height
    height_range = (140.0, 210.0)
    numeric_choice = 175.0
    assert height_range[0] <= numeric_choice <= height_range[1]

    # Input sequence:
    # name, race index, class index, traits csv,
    # appearance: eye_color index (1), height value (numeric), then accept defaults for remainder
    inputs = iter(
        [
            "CliHero",  # name
            "1",  # race index
            "1",  # class index
            "brave,lucky",  # traits CSV
            "1",  # eye_color -> first option
            str(numeric_choice),  # height_cm
            # consume prompts for all other fields quickly using 'd' for default
            *(["d"] * 20),
            "",  # save path default (if prompted anywhere)
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda *_args, **_kwargs: next(inputs))

    hero = run_wizard(loaders_dict)
    # Validate selections applied
    assert hero.appearance.get("eye_color") is not None
    assert isinstance(hero.appearance.get("height_cm"), (int, float))
    assert height_range[0] <= float(hero.appearance["height_cm"]) <= height_range[1]
