from __future__ import annotations

from pathlib import Path
import sys

from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    items_loader,
    appearance_loader,
    races_loader,
)
from character_creation.services.validate_data import (
    DataValidationError,
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


def main() -> int:
    root = Path(__file__).parents[1] / "character_creation" / "data"
    try:
        # Load core data
        stats = stats_loader.load_stat_template(root / "stats" / "stats.yaml")
        classes = classes_loader.load_class_catalog(root / "classes.yaml")
        traits = traits_loader.load_trait_catalog(root / "traits.yaml")
        slots = slots_loader.load_slot_template(root / "slots.yaml")
        items = (
            items_loader.load_item_catalog(root / "items.yaml")
            if (root / "items.yaml").exists()
            else {}
        )
        races = races_loader.load_race_catalog(root / "races.yaml")
        appearance_fields = appearance_loader.load_appearance_fields(
            root / "appearance" / "fields.yaml"
        )
        # defaults/resources are optional for validation and not required here
        # One table and one range, if available
        tables_dir = root / "appearance" / "tables"
        ranges_dir = root / "appearance" / "ranges"
        any_table = None
        any_table_name = None
        if tables_dir.exists():
            for p in tables_dir.glob("*.yaml"):
                any_table = appearance_loader.load_enum(p.name, base_dir=tables_dir)
                any_table_name = p.name
                break
        any_range = None
        any_range_name = None
        if ranges_dir.exists():
            for p in ranges_dir.glob("*.yaml"):
                any_range = appearance_loader.load_range(p.name, base_dir=ranges_dir)
                any_range_name = p.name
                break
        # Creation limits
        limits_path = root / "creation_limits.yaml"
        limits = {}
        if limits_path.exists():
            from character_creation.loaders.yaml_utils import load_yaml

            limits = load_yaml(limits_path)

        # Run validators
        validate_stats(stats)
        validate_classes(classes)
        validate_traits(traits)
        validate_slots(slots)
        if items:
            validate_items(items, slots)
        validate_races(races)
        validate_appearance_fields(appearance_fields)
        if any_table is not None and any_table_name is not None:
            validate_appearance_table(any_table, any_table_name)
        if any_range is not None and any_range_name is not None:
            validate_numeric_range(any_range, any_range_name)
        if limits:
            validate_creation_limits(limits)
        print("OK")
        return 0
    except DataValidationError as e:
        print(f"Validation failed: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
