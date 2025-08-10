from typing import Dict, List
from ...models.factory import create_new_character
from ...services.creation_logic import available_starting_classes, validate_traits


def ask_name() -> str:
    while True:
        name = input("Enter character name: ").strip()
        if name:
            return name
        print("Name cannot be empty. Please enter a valid name.")


def choose_starting_class(class_list: List[dict]) -> dict:
    while True:
        print("Choose a starting class:")
        for idx, cls in enumerate(class_list, 1):
            print(f"{idx}. {cls.get('name', cls.get('id', 'Unknown'))}")
        choice = input(f"Enter number (1-{len(class_list)}): ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(class_list):
                return class_list[idx - 1]
        print("Invalid choice. Try again.")


def choose_traits(trait_catalog: Dict[str, dict], max_count: int = 2) -> List[str]:
    traits = trait_catalog.get("traits", {})
    print("Available traits:")
    for tid, tdef in traits.items():
        print(f"{tid}: {tdef.get('name', tid)}")
    while True:
        ids = input(f"Enter up to {max_count} trait ids (comma-separated): ").strip()
        selected = [tid.strip() for tid in ids.split(",") if tid.strip()]
        selected = list(dict.fromkeys(selected))  # dedupe, preserve order
        if len(selected) > max_count:
            print(f"Please select no more than {max_count} traits.")
            continue
        valid = validate_traits(selected, trait_catalog)
        if valid:
            return valid
        print("No valid traits selected. Try again.")


def confirm_save_path(default_path: str) -> str:
    path = input(f"Enter save path (default: {default_path}): ").strip()
    return path if path else default_path


def choose_race(race_catalog: dict) -> dict:
    """
    Show numbered list of races (use 'name' if present else id), prompt until valid index,
    return chosen race dict.
    """
    races = list(race_catalog.get("races", []))
    if not races:
        return {}
    while True:
        print("Choose a race:")
        for idx, race in enumerate(races, 1):
            label = race.get("name") or race.get("id") or "Unknown"
            print(f"{idx}. {label}")
        choice = input(f"Enter number (1-{len(races)}): ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(races):
                return races[idx - 1]
        print("Invalid choice. Try again.")


def run_wizard(loaders_dict: dict):
    name = ask_name()
    stat_tmpl = loaders_dict["stat_tmpl"]
    slot_tmpl = loaders_dict["slot_tmpl"]
    appearance_fields = loaders_dict["appearance_fields"]
    appearance_defaults = loaders_dict.get("appearance_defaults", {})
    resources = loaders_dict["resources"]
    class_catalog = loaders_dict["class_catalog"]
    trait_catalog = loaders_dict["trait_catalog"]
    race_catalog = loaders_dict.get("race_catalog", {"races": []})
    starting_classes = available_starting_classes(stat_tmpl, class_catalog)
    race_def = choose_race(race_catalog)
    class_def = choose_starting_class(starting_classes)
    traits = choose_traits(trait_catalog)
    character = create_new_character(
        name, stat_tmpl, slot_tmpl, appearance_fields, appearance_defaults, resources
    )
    if race_def:
        rid = race_def.get("id")
        if rid:
            character.set_race(rid, race_catalog)
    character.add_class(class_def)
    # Apply trait effects and store IDs only
    character.add_traits(traits, trait_catalog)
    return character
