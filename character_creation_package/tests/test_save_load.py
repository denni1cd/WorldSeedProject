from pathlib import Path
import yaml

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
)
from character_creation.models.factory import create_new_character
from character_creation.models.character import Character


def setup_character():
    root = Path(__file__).parents[1] / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(
        root / "appearance" / "fields.yaml"
    )
    defaults = appearance_loader.load_appearance_defaults(
        root / "appearance" / "defaults.yaml"
    )
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    formulas = yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))
    hero = create_new_character(
        "SaveTest",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )
    return hero


def test_save_and_load(tmp_path: Path):
    hero = setup_character()
    save_file = tmp_path / "hero.yaml"
    hero.save(save_file)
    assert save_file.exists()
    loaded = Character.load(save_file)
    assert loaded.name == hero.name
    assert loaded.hp == hero.hp
