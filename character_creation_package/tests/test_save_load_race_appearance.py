from pathlib import Path
import yaml

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    races_loader,
)
from character_creation.models.factory import create_new_character
from character_creation.models.character import Character


def test_save_load_includes_race_and_appearance(tmp_path: Path):
    root = Path(__file__).parents[1] / "character_creation" / "data"
    stat_tmpl = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(root / "slots.yaml")
    fields = appearance_loader.load_appearance_fields(root / "appearance" / "fields.yaml")
    defaults = appearance_loader.load_appearance_defaults(root / "appearance" / "defaults.yaml")
    resources = resources_loader.load_resources(root / "resources.yaml")
    progression = progression_loader.load_progression(root / "progression.yaml")
    formulas = yaml.safe_load(open(root / "formulas.yaml", "r", encoding="utf-8"))
    races = races_loader.load_race_catalog(root / "races.yaml")

    hero = create_new_character(
        "RoundTrip",
        stat_tmpl,
        slot_tmpl,
        fields,
        defaults,
        resources,
        progression=progression,
        formulas=formulas,
    )

    race_id = races.get("races", [{}])[0].get("id") if races.get("races") else None
    if race_id:
        hero.set_race(race_id, races)

    # apply a couple appearance selections
    spec = fields.get("fields", fields)
    if "eye_color" in spec:
        hero.appearance["eye_color"] = spec["eye_color"].get("default", "brown")
    if "height_cm" in spec:
        hero.appearance["height_cm"] = spec["height_cm"].get("default", 170)

    dest = tmp_path / "rt.yaml"
    hero.save(dest)
    assert dest.exists()

    loaded = Character.load(dest)
    assert loaded.name == hero.name
    assert loaded.race == hero.race
    for k, v in hero.appearance.items():
        assert loaded.appearance.get(k) == v
