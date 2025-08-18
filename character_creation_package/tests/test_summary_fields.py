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
from character_creation.ui.cli import wizard as wiz


DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"
CHAR = DATA_ROOT / "character"
BACK = DATA_ROOT / "backend"


def pick(*candidates: Path) -> Path:
    for p in candidates:
        try:
            if p.exists():
                return p
        except Exception:
            continue
    return candidates[-1]


@pytest.fixture
def loaders_dict():
    return {
        "stat_tmpl": stats_loader.load_stat_template(
            pick(CHAR / "stats" / "stats.yaml", DATA_ROOT / "stats" / "stats.yaml")
        ),
        "class_catalog": classes_loader.load_class_catalog(
            pick(CHAR / "classes.yaml", DATA_ROOT / "classes.yaml")
        ),
        "trait_catalog": traits_loader.load_trait_catalog(
            pick(CHAR / "traits.yaml", DATA_ROOT / "traits.yaml")
        ),
        "race_catalog": races_loader.load_race_catalog(
            pick(CHAR / "races.yaml", DATA_ROOT / "races.yaml")
        ),
        "slot_tmpl": slots_loader.load_slot_template(
            pick(BACK / "slots.yaml", DATA_ROOT / "slots.yaml")
        ),
        "appearance_fields": appearance_loader.load_appearance_fields(
            pick(CHAR / "appearance" / "fields.yaml", DATA_ROOT / "appearance" / "fields.yaml")
        ),
        "appearance_defaults": appearance_loader.load_appearance_defaults(
            pick(CHAR / "appearance" / "defaults.yaml", DATA_ROOT / "appearance" / "defaults.yaml")
        ),
        "resources": resources_loader.load_resources(
            pick(BACK / "resources.yaml", DATA_ROOT / "resources.yaml")
        ),
    }


def test_cli_summary_contains_required_fields(monkeypatch, capsys, loaders_dict):
    # Inputs through the wizard up to save prompt; _safe_input uses defaults for appearance
    inputs = iter(
        [
            "SummaryHero",  # name
            "1",  # race
            "1",  # class
            "brave, lucky",  # traits
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(wiz, "_safe_input", lambda prompt: "d")

    hero = wiz.run_wizard(loaders_dict)
    assert hero.name == "SummaryHero"

    out = capsys.readouterr().out
    # Required lines
    assert "Name: SummaryHero" in out
    assert "Race: " in out
    assert "Class: " in out
    assert "Traits: " in out and ("Brave" in out or "brave" in out)
    assert "HP/Mana:" in out
    # At least 3 appearance fields
    assert "Appearance:" in out
    # Check 3 keys present
    for key in ["eye=", "hair=", "height=", "weight="]:
        assert key in out
