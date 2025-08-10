from pathlib import Path

from character_creation.services.live_reload import CatalogReloader


def test_reload_once_loads_and_validates():
    dr = Path("character_creation/data")
    rel = CatalogReloader(dr)
    cats = rel.reload_once()
    assert "class_catalog" in cats and "trait_catalog" in cats
    assert isinstance(cats["class_catalog"].get("classes", []), list)
    assert isinstance(cats["trait_catalog"].get("traits", {}), dict)
    assert rel.version >= 1
