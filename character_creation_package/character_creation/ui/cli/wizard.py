from typing import Any, Dict, List
from pathlib import Path
from ...models.factory import create_new_character
from ...services.creation_logic import available_starting_classes, validate_traits
from ...services import random_utils
from ...services.appearance_logic import (
    get_enum_values,
    get_numeric_bounds,
    coerce_numeric,
    default_for_field,
)
from ...loaders.yaml_utils import load_yaml


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
            return valid[:max_count]
        print("No valid traits selected. Try again.")


def _resolve_appearance_dir() -> Path:
    # character_creation/ui/cli/wizard.py -> .../character_creation/data/appearance
    return Path(__file__).parents[3] / "character_creation" / "data" / "appearance"


def _safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except Exception:
        # Fallback to default command when inputs are exhausted (e.g., tests)
        return "d"


def _load_creation_limits() -> dict:
    """Load creation_limits.yaml if present; return dict with defaults on failure."""
    try:
        # character_creation/ui/cli/wizard.py -> .../character_creation/data/creation_limits.yaml
        limits_path = (
            Path(__file__).parents[3] / "character_creation" / "data" / "creation_limits.yaml"
        )
        if limits_path.exists():
            data = load_yaml(limits_path)
        else:
            data = {}
    except Exception:
        data = {}
    lm = data.get("limits", data) if isinstance(data, dict) else {}
    # Safe defaults
    return {"traits_max": int(lm.get("traits_max", 2))}


def choose_appearance(
    appearance_fields: Dict[str, dict],
    defaults: Dict[str, Any],
    data_dir: str | Path,
) -> Dict[str, Any]:
    """
    For each field in appearance_fields:
      - If enum: print choices (1..N) from tables; allow entering number or value; allow 'd' for default, 'r' for random.
      - If float: show min/max; prompt for number; allow 'd' (default) and 'r' (random within range).
    Return dict {field_id: chosen_value}.
    Implement simple re-prompt on invalid inputs.
    """

    base_dir = Path(data_dir)
    spec = appearance_fields.get("fields", appearance_fields)
    selections: Dict[str, Any] = {}
    # Optional extra appearance tables from content packs
    try:
        extra_tables = appearance_fields.get("_extra_appearance_tables")
    except Exception:
        extra_tables = None

    for field_id, meta in spec.items():
        ftype = meta.get("type", "any")
        default_val = default_for_field(field_id, appearance_fields, defaults)

        # Skip opaque types (any) — keep default
        if ftype not in {"enum", "float", "number", "int"}:
            if field_id not in selections:
                selections[field_id] = default_val
            continue

        while True:
            if ftype == "enum":
                values = get_enum_values(field_id, appearance_fields, base_dir, extra_tables)
                if not values:
                    print(f"[warn] No table for enum field '{field_id}', using default")
                    selections[field_id] = default_val
                    break
                print(f"Choose {field_id}:")
                for idx, val in enumerate(values, 1):
                    print(f"  {idx}. {val}")
                prompt = f"Enter number (1-{len(values)}), value, 'd' default, or 'r' random: "
                raw = _safe_input(prompt).strip()
                if raw.lower() == "d":
                    selections[field_id] = default_val
                    break
                if raw.lower() == "r":
                    picked = random_utils.choice(values)
                    # Convert 'null' sentinel to None
                    selections[field_id] = None if picked == "null" else picked
                    break
                if raw.isdigit():
                    idx = int(raw)
                    if 1 <= idx <= len(values):
                        val = values[idx - 1]
                        selections[field_id] = None if val == "null" else val
                        break
                # Accept direct value if valid
                if raw in values:
                    selections[field_id] = None if raw == "null" else raw
                    break
                print("Invalid input. Try again.")
                continue

            # Numeric
            bounds = get_numeric_bounds(field_id, appearance_fields, base_dir)
            if not bounds:
                print(f"[warn] No bounds for numeric field '{field_id}', using default")
                selections[field_id] = default_val
                break
            min_v, max_v = bounds
            print(f"Set {field_id} (min {min_v}, max {max_v}) — 'd' default, 'r' random:")
            raw = _safe_input("Enter number or command: ").strip().lower()
            if raw == "d":
                selections[field_id] = coerce_numeric(default_val, min_v, max_v)
                break
            if raw == "r":
                # Prefer uniform within [min,max]
                selections[field_id] = float(random_utils.roll_uniform(min_v, max_v))
                break
            try:
                val = float(raw)
                selections[field_id] = coerce_numeric(val, min_v, max_v)
                break
            except Exception:
                print("Invalid number. Try again.")
                continue

    return selections


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
    # Load creation limits (safe defaults if missing)
    limits = _load_creation_limits()
    traits_max = int(limits.get("traits_max", 2))

    race_def = choose_race(race_catalog)
    class_def = choose_starting_class(starting_classes)
    traits = choose_traits(trait_catalog, max_count=traits_max)
    # Appearance step
    try:
        app_dir = _resolve_appearance_dir()
    except Exception:
        app_dir = Path(".")
    appearance_selection = choose_appearance(appearance_fields, appearance_defaults, app_dir)
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
    # Apply appearance selections
    try:
        character.appearance.update(appearance_selection)
    except Exception:
        pass

    # Compact summary before save prompt (done by caller)
    try:
        race_label = (race_def.get("name") or race_def.get("id")) if race_def else ""
    except Exception:
        race_label = ""
    try:
        class_label = class_def.get("name") or class_def.get("id") or ""
    except Exception:
        class_label = ""
    # Trait names
    trait_meta = (trait_catalog or {}).get("traits", {})
    trait_names = []
    for tid in getattr(character, "traits", []) or []:
        meta = trait_meta.get(tid, {})
        trait_names.append(meta.get("name") or tid)
    trait_csv = ", ".join(trait_names)
    # HP/Mana current/base
    hp_line = (
        f"{getattr(character, 'hp', 0)}/{getattr(character, 'hp_max', getattr(character, 'hp', 0))}"
    )
    mana_line = f"{getattr(character, 'mana', 0)}/{getattr(character, 'mana_max', getattr(character, 'mana', 0))}"
    # Core stats
    stats = getattr(character, "stats", {}) or {}
    core_keys = ["STR", "DEX", "INT", "CHA", "STA"]
    core_pairs = [f"{k}={stats.get(k)}" for k in core_keys if k in stats]
    stats_line = " ".join(core_pairs)
    # Appearance peek
    app = getattr(character, "appearance", {}) or {}
    eye = app.get("eye_color")
    hair = app.get("hair_color")
    height = app.get("height_cm")
    weight = app.get("weight_kg")
    appearance_line = ", ".join(
        [
            f"eye={eye}",
            f"hair={hair}",
            f"height={height}",
            f"weight={weight}",
        ]
    )

    print(f"Name: {character.name}")
    print(f"Race: {race_label}")
    print(f"Class: {class_label}")
    print(f"Traits: {trait_csv}")
    print(f"HP/Mana: {hp_line} | {mana_line}")
    print(f"Stats: {stats_line}")
    print(f"Appearance: {appearance_line}")

    return character
