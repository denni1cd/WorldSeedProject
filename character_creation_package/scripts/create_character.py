from pathlib import Path
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from character_creation.ui.cli.wizard import run_wizard, confirm_save_path


def main() -> None:
    root = Path(__file__).parents[1]
    # Resolve data paths
    stats_path = root / "character_creation" / "data" / "stats" / "stats.yaml"
    classes_path = root / "character_creation" / "data" / "classes.yaml"
    traits_path = root / "character_creation" / "data" / "traits.yaml"
    slots_path = root / "character_creation" / "data" / "slots.yaml"
    fields_path = root / "character_creation" / "data" / "appearance" / "fields.yaml"
    defaults_path = root / "character_creation" / "data" / "appearance" / "defaults.yaml"
    resources_path = root / "character_creation" / "data" / "resources.yaml"

    # Load YAML data
    stat_tmpl = stats_loader.load_stat_template(stats_path)
    class_catalog = classes_loader.load_class_catalog(classes_path)
    trait_catalog = traits_loader.load_trait_catalog(traits_path)
    slot_tmpl = slots_loader.load_slot_template(slots_path)
    fields = appearance_loader.load_appearance_fields(fields_path)
    defaults = appearance_loader.load_appearance_defaults(defaults_path)
    resources = resources_loader.load_resources(resources_path)

    # Run wizard
    hero = run_wizard(
        {
            "stat_tmpl": stat_tmpl,
            "slot_tmpl": slot_tmpl,
            "appearance_fields": fields,
            "appearance_defaults": defaults,
            "resources": resources,
            "classes_loader": class_catalog,
            "traits_loader": trait_catalog,
        }
    )

    # Ask for save path
    default_path = str(root / "hero.json")
    save_path = confirm_save_path(default_path)
    hero.to_json(save_path)
    print(f"Character saved to {save_path}")


if __name__ == "__main__":
    main()
