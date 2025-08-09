import sys
from pathlib import Path
from character_creation.loaders import (
    yaml_utils,
    classes_loader,
    traits_loader,
)
from character_creation.models import npc_factory

# This is a common pattern for scripts in a subdirectory to ensure
# they can import modules from the parent package.
# It adds the 'character_creation_package' directory to Python's path.
PACKAGE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PACKAGE_ROOT))


def main():
    """
    Main function to load data, generate NPCs, and print their details.
    """
    # Define the base path for data files
    data_path = PACKAGE_ROOT / "character_creation" / "data"

    # Load all necessary data files
    try:
        stat_tmpl = yaml_utils.load_yaml(data_path / "stats" / "stats.yaml")
        slot_tmpl = yaml_utils.load_yaml(data_path / "slots.yaml")
        appearance_fields = yaml_utils.load_yaml(data_path / "appearance" / "fields.yaml")
        class_catalog = classes_loader.load_class_catalog(data_path / "classes.yaml").get(
            "classes", []
        )
        trait_catalog = traits_loader.load_trait_catalog(data_path / "traits.yaml").get(
            "traits", {}
        )
        resources = yaml_utils.load_yaml(data_path / "resources.yaml")
        formulas = yaml_utils.load_yaml(data_path / "formulas.yaml")
        appearance_tables_dir = data_path / "appearance" / "tables"
        appearance_ranges_dir = data_path / "appearance" / "ranges"
    except FileNotFoundError as e:
        print(
            f"Error loading data file: {e}. Make sure you are running the script from the correct directory."
        )
        sys.exit(1)

    print("--- Generating 3 NPCs ---")

    for i in range(1, 4):
        # Generate a single NPC
        npc = npc_factory.generate_npc(
            name_prefix=f"NPC_{i}",
            stat_tmpl=stat_tmpl,
            slot_tmpl=slot_tmpl,
            appearance_fields=appearance_fields,
            appearance_tables_dir=appearance_tables_dir,
            appearance_ranges_dir=appearance_ranges_dir,
            class_catalog=class_catalog,
            trait_catalog=trait_catalog,
            resources=resources,
            formulas=formulas,
        )

        # Print the generated NPC's details
        print(f"\n--- Details for {npc.name} ---")
        print(f"  Level: {npc.level}")
        print(f"  HP: {npc.stats['HP'].current}/{npc.stats['HP'].base}")
        print(f"  Mana: {npc.stats['Mana'].current}/{npc.stats['Mana'].base}")
        print(f"  Classes: {[ (c.get('name') or c.get('id') or 'Unknown') for c in npc.classes ]}")
        print(f"  Traits: {[ (t.get('name') or t.get('id') or 'Unknown') for t in npc.traits ]}")
        # Printing the full stats dictionary can be verbose, let's show a summary
        stats_summary = {
            name: f"{s.current:.1f}" for name, s in npc.stats.items() if name not in ["HP", "Mana"]
        }
        print(f"  Stats: {stats_summary}")
        print("-" * 20)


if __name__ == "__main__":
    main()
