from pathlib import Path
import yaml
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    items_loader,
    races_loader,
    appearance_loader,
)
from character_creation.services.validate_data import (
    validate_stats,
    validate_classes,
    validate_traits,
    validate_slots,
    validate_items,
    validate_races,
    validate_appearance_fields,
    validate_appearance_table,
    validate_numeric_range,
    validate_creation_limits,
)


def test_yaml_validates():
    root = Path(__file__).resolve().parents[1] / "character_creation" / "data"
    stats = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
    classes = classes_loader.load_class_catalog(root / "classes.yaml")
    traits = traits_loader.load_trait_catalog(root / "traits.yaml")
    slots = slots_loader.load_slot_template(root / "slots.yaml")
    items = items_loader.load_item_catalog(root / "items.yaml")
    validate_stats(stats)
    validate_classes(classes)
    validate_traits(traits)
    validate_slots(slots)
    validate_items(items, slots)


def test_races_and_appearance_validate():
    root = Path(__file__).resolve().parents[1] / "character_creation" / "data"
    races = races_loader.load_race_catalog(root / "races.yaml")
    validate_races(races)

    fields = appearance_loader.load_appearance_fields(
        root / "appearance" / "fields.yaml"
    )
    validate_appearance_fields(fields)

    tables_dir = root / "appearance" / "tables"
    ranges_dir = root / "appearance" / "ranges"
    if tables_dir.exists():
        for p in tables_dir.glob("*.yaml"):
            values = yaml.safe_load(open(p, "r", encoding="utf-8"))
            validate_appearance_table(values, p.stem)
            break
    if ranges_dir.exists():
        for p in ranges_dir.glob("*.yaml"):
            rng = yaml.safe_load(open(p, "r", encoding="utf-8"))
            validate_numeric_range(rng, p.stem)
            break

    limits_path = root / "creation_limits.yaml"
    if limits_path.exists():
        limits = yaml.safe_load(open(limits_path, "r", encoding="utf-8")) or {}
        validate_creation_limits(limits)
