import builtins
from pathlib import Path

from character_creation.loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    classes_loader,
    traits_loader,
    races_loader,
)
from character_creation.loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)
from character_creation.ui.cli.wizard import run_wizard


DATA_ROOT = Path(__file__).parents[2] / "character_creation_package" / "character_creation" / "data"


def test_wizard_can_select_pack_race_and_class(monkeypatch, tmp_path):
    # Base
    stat_tmpl = stats_loader.load_stat_template(DATA_ROOT / "stats" / "stats.yaml")
    slot_tmpl = slots_loader.load_slot_template(DATA_ROOT / "slots.yaml")
    appearance_fields = appearance_loader.load_appearance_fields(
        DATA_ROOT / "appearance" / "fields.yaml"
    )
    appearance_defaults = appearance_loader.load_appearance_defaults(
        DATA_ROOT / "appearance" / "defaults.yaml"
    )
    resources = resources_loader.load_resources(DATA_ROOT / "resources.yaml")
    base_classes = classes_loader.load_class_catalog(DATA_ROOT / "classes.yaml")
    base_traits = traits_loader.load_trait_catalog(DATA_ROOT / "traits.yaml")
    base_races = races_loader.load_race_catalog(DATA_ROOT / "races.yaml")

    # Merge packs
    packs_cfg = load_packs_config(DATA_ROOT / "content_packs.yaml")
    merged_overlay = load_and_merge_enabled_packs(DATA_ROOT, packs_cfg)
    policy = packs_cfg.get("merge", {}).get("on_conflict", "skip")
    base = {
        "classes": base_classes.get("classes", base_classes),
        "traits": base_traits.get("traits", base_traits),
        "races": base_races.get("races", base_races),
    }
    merged_all = merge_catalogs(base, merged_overlay, on_conflict=policy)
    class_catalog = {"classes": merged_all.get("classes", [])}
    trait_catalog = {"traits": merged_all.get("traits", {})}
    race_catalog = {"races": merged_all.get("races", [])}

    # Find indices of a pack-provided entry by name or id
    pack_class_id = None
    for cls in class_catalog["classes"]:
        if cls.get("id") in {
            "duelist",
            "battlemage",
            "ranger",
            "bard",
            "paladin",
            "monk",
            "necromancer",
            "druid",
            "barbarian",
            "assassin",
            "chronomancer",
            "sentinel",
        }:
            pack_class_id = cls["id"]
            break
    assert pack_class_id is not None, "Expected a pack-provided class id"

    pack_race_id = None
    for r in race_catalog["races"]:
        if r.get("id") in {
            "gnome",
            "tiefling",
            "aasimar",
            "lizardfolk",
            "goblin",
            "kitsune",
            "automaton",
        }:
            pack_race_id = r["id"]
            break
    assert pack_race_id is not None, "Expected a pack-provided race id"

    # Map to visible indices in CLI lists (1-based)
    class_index_1based = None
    for idx, cls in enumerate(class_catalog["classes"], 1):
        if cls.get("id") == pack_class_id and not cls.get("prereq"):
            class_index_1based = idx
            break
    assert class_index_1based is not None

    race_index_1based = None
    for idx, r in enumerate(race_catalog["races"], 1):
        if r.get("id") == pack_race_id:
            race_index_1based = idx
            break
    assert race_index_1based is not None

    # Inputs: name, pick race index, pick class index, provide a valid trait id (e.g., 'brave')
    inputs = iter(["PackHero", str(race_index_1based), str(class_index_1based), "brave"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    hero = run_wizard(
        {
            "stat_tmpl": stat_tmpl,
            "slot_tmpl": slot_tmpl,
            "appearance_fields": appearance_fields,
            "appearance_defaults": appearance_defaults,
            "resources": resources,
            "class_catalog": class_catalog,
            "trait_catalog": trait_catalog,
            "race_catalog": race_catalog,
        }
    )

    assert hero.name == "PackHero"
    assert hero.race == pack_race_id
    assert hero.classes and pack_class_id in hero.classes
