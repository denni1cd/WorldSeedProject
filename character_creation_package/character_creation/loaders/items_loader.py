from pathlib import Path
from typing import Any, Dict
import yaml


def load_item_catalog(path: str | Path) -> Dict[str, Any]:
    """
    Load the item catalog from a YAML file and return the dictionary under the 'items' key.
    Args:
        path (str | Path): Path to the YAML file.
    Returns:
        Dict[str, Any]: Dictionary containing the items catalog.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", {})
