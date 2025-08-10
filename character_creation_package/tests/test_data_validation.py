from pathlib import Path
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    items_loader,
)
from character_creation.services.validate_data import (
    validate_stats,
    validate_classes,
    validate_traits,
    validate_slots,
    validate_items,
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
