from typing import Dict, List
from ...models.factory import create_new_character
from ...services.creation_logic import available_starting_classes, validate_traits


def ask_name() -> str:
    name = input("Enter character name: ").strip()
    return name


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


def run_wizard(loaders_dict: dict):
    name = ask_name()
    stat_tmpl = loaders_dict["stats_loader"]
    class_catalog = loaders_dict["classes_loader"]
    trait_catalog = loaders_dict["traits_loader"]
    starting_classes = available_starting_classes(stat_tmpl, class_catalog)
    class_def = choose_starting_class(starting_classes)
    traits = choose_traits(trait_catalog)
    character = create_new_character(name=name)
    character.add_class(class_def)
    character.add_traits(traits)
    return character
