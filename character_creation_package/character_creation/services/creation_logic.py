from typing import Dict, List


def available_starting_classes(
    stat_tmpl: Dict[str, dict], class_catalog: Dict[str, list]
) -> List[dict]:
    """
    Return class blocks from class_catalog["classes"] that have empty prereq (or no prereq key).
    This is just for start-of-game picks.
    """
    classes = class_catalog.get("classes", [])
    return [cls for cls in classes if not cls.get("prereq")]


def validate_traits(selected_ids: List[str], trait_catalog: Dict[str, dict]) -> List[str]:
    """
    Return a deduplicated list of trait ids that exist in trait_catalog["traits"].
    Ignore unknown ids.
    """
    traits = trait_catalog.get("traits", {})
    valid_ids = set(selected_ids)
    return [tid for tid in valid_ids if tid in traits]


def get_default_stats(stat_tmpl: Dict[str, dict]) -> Dict[str, int]:
    """
    Return a dict of stat names to their default values from stat_tmpl.
    """
    return {k: v.get("default", 0) for k, v in stat_tmpl.items()}


def get_default_xp(stat_tmpl: Dict[str, dict]) -> int:
    """
    Return the default XP value from stat_tmpl if present, else 0.
    """
    return stat_tmpl.get("xp", {}).get("default", 0)
