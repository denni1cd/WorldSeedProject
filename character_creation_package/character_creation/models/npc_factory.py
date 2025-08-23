# character_creation/models/npc_factory.py

import random
import uuid
from pathlib import Path
from typing import Any, Dict, List

from character_creation.models.character import Character
from character_creation.models import factory
from character_creation.services import formula_eval, random_utils
from character_creation.services.seed import set_seed
from character_creation.loaders import yaml_utils


def _add_stat_value(character: Character, stat_name: str, delta: float) -> None:
    """
    Add `delta` to a stat, regardless of whether the stat is an object (.base/.current),
    a dict with 'base'/'current', or a plain number. Gracefully no-op if unknown.
    """
    if stat_name not in character.stats:
        return

    val = character.stats[stat_name]

    # Object with attributes
    if hasattr(val, "base") and hasattr(val, "current"):
        val.base += delta
        val.current += delta
        return

    # Dict with keys
    if isinstance(val, dict) and "base" in val and "current" in val:
        val["base"] += delta
        val["current"] += delta
        return

    # Numeric fallback
    try:
        base_val = float(val) if isinstance(val, (int, float, str)) else 0.0
        character.stats[stat_name] = base_val + delta
    except Exception:
        pass


def _add_abilities(collection: Any, abilities: List[str]) -> None:
    """Add ability names to either a set or list, de-duplicating when needed."""
    if not abilities or collection is None:
        return
    if isinstance(collection, set):
        collection.update(abilities)
    elif isinstance(collection, list):
        for a in abilities:
            if a not in collection:
                collection.append(a)


def _append_collection(collection: Any, item: Any) -> None:
    """Append to list or add to set (store id/name if dict when adding to a set)."""
    if collection is None:
        return
    if isinstance(collection, list):
        collection.append(item)
    elif isinstance(collection, set):
        if isinstance(item, dict):
            key = item.get("id") or item.get("name") or str(item)
            collection.add(key)
        else:
            collection.add(item)


def _stat_value_for_ctx(v: Any) -> float:
    """Extract a numeric 'current' value from various stat representations for formula context."""
    if hasattr(v, "current"):
        return float(v.current)
    if isinstance(v, dict) and "current" in v:
        return float(v["current"])
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except Exception:
        return 0.0


def generate_npc(
    name_prefix: str,
    stat_tmpl: Dict[str, Any],
    slot_tmpl: Dict[str, Any],
    appearance_fields: Dict[str, Any],
    appearance_tables_dir: Path,
    appearance_ranges_dir: Path,
    class_catalog: List[Dict[str, Any]],
    trait_catalog: Dict[str, Any],
    resources: Dict[str, Any],
    formulas: Dict[str, Any],
    seed: int | None = None,
) -> Character:
    """
    Generates a complete NPC character with randomized attributes.
    """

    # 0) Optional deterministic seeding
    set_seed(seed)

    # 1) Randomize stats from template
    randomized_stats = {k: v.copy() for k, v in stat_tmpl.items()}
    for stat_data in randomized_stats.values():
        bumps = random.randint(0, 3)
        stat_data["initial"] += bumps * 0.1

    # 2) Choose class and traits
    if not class_catalog:
        raise ValueError("Class catalog is empty, cannot generate NPC.")
    starter_class = random_utils.choice(
        class_catalog
    )  # dict: {id, grants_stats, grants_abilities, ...}

    # trait_catalog is a mapping with key 'traits' -> dict of trait_id -> def
    trait_names = list(trait_catalog.get("traits", {}).keys())
    max_traits = min(len(trait_names), 2)
    num_traits = random.randint(0, max_traits)
    chosen_trait_names = random.sample(trait_names, k=num_traits)

    # 3) Load appearance defaults (sibling to fields.yaml)
    # appearance_tables_dir = .../appearance/tables  -> parent is .../appearance
    appearance_defaults_path = appearance_tables_dir.parent / "defaults.yaml"
    appearance_defaults = (
        yaml_utils.load_yaml(appearance_defaults_path) if appearance_defaults_path.exists() else {}
    )

    # 4) Create the character
    unique_id = str(uuid.uuid4()).split("-")[0]
    npc_name = f"{name_prefix}_{unique_id}"
    character = factory.create_new_character(
        name=npc_name,
        stat_tmpl=randomized_stats,
        slot_tmpl=slot_tmpl,
        appearance_fields=appearance_fields,
        appearance_defaults=appearance_defaults,
        resources=resources,
    )

    # 5) Apply class and traits via Character API (IDs only, effects inside)
    character.add_class(starter_class)
    character.add_traits(chosen_trait_names, trait_catalog)

    # 7) Roll random appearance values (override defaults where appropriate)
    for field_name, field_info in appearance_fields.items():
        field_type = field_info.get("type")
        if field_type == "enum":
            table_file_name = field_info.get("table_file")
            if table_file_name:
                table_file = appearance_tables_dir / table_file_name
                if table_file.exists():
                    values = yaml_utils.load_yaml(table_file)
                    character.appearance[field_name] = random_utils.choice(values)
                    continue
            # Fallbacks if table missing
            if "default" in field_info and field_info["default"] is not None:
                character.appearance[field_name] = field_info["default"]
            else:
                character.appearance[field_name] = "Unknown"
        elif field_type == "float":
            range_file_name = field_info.get("range_file")
            if range_file_name:
                range_file = appearance_ranges_dir / range_file_name
                if range_file.exists():
                    range_data = yaml_utils.load_yaml(range_file)
                    dist_key = f"{field_name}_distribution"
                    distribution = formulas.get("rng", {}).get(dist_key, "uniform")
                    if distribution == "normal":
                        character.appearance[field_name] = random_utils.roll_normal(
                            mean=range_data.get("mean", 0.0),
                            sd=range_data.get("sd", 1.0),
                        )
                    else:
                        character.appearance[field_name] = random_utils.roll_uniform(
                            min_val=range_data.get("min", 0.0),
                            max_val=range_data.get("max", 1.0),
                        )
                    continue
            # Fallbacks if range missing
            if "default" in field_info and field_info["default"] is not None:
                character.appearance[field_name] = field_info["default"]
            else:
                # deterministic enough for tests but non-None
                character.appearance[field_name] = random_utils.roll_uniform(0.0, 1.0)
        else:
            # For 'any' and other types, keep defaults or set to a non-None placeholder
            if field_name not in character.appearance or character.appearance[field_name] is None:
                character.appearance[field_name] = field_info.get("default", "")

    # 8) Set starting level
    character.level = 1

    # 9) Recalculate HP/Mana via formulas
    ctx = {"level": character.level}
    for s_name, s_val in character.stats.items():
        ctx[s_name] = _stat_value_for_ctx(s_val)

    hp_val = int(formula_eval.evaluate(formulas["baseline"]["hp"], ctx))
    mana_val = int(formula_eval.evaluate(formulas["baseline"]["mana"], ctx))

    # Set HP
    hp_obj = character.stats.get("HP")
    if hasattr(hp_obj, "base") and hasattr(hp_obj, "current"):
        hp_obj.base = hp_val
        hp_obj.current = hp_val
    elif isinstance(hp_obj, dict):
        hp_obj["base"] = hp_val
        hp_obj["current"] = hp_val
    else:
        character.stats["HP"] = {"base": hp_val, "current": hp_val}

    # Set Mana
    mana_obj = character.stats.get("Mana")
    if hasattr(mana_obj, "base") and hasattr(mana_obj, "current"):
        mana_obj.base = mana_val
        mana_obj.current = mana_val
    elif isinstance(mana_obj, dict):
        mana_obj["base"] = mana_val
        mana_obj["current"] = mana_val
    else:
        character.stats["Mana"] = {"base": mana_val, "current": mana_val}

    # XP to next
    character.xp_to_next_level = int(formula_eval.evaluate(formulas["baseline"]["xp_to_next"], ctx))

    return character
