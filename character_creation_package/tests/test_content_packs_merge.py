from pathlib import Path

from character_creation.loaders import (
    classes_loader,
    traits_loader,
    races_loader,
)
from character_creation.loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)
from character_creation.services.validate_data import validate_merged_catalogs


DATA_ROOT = (
    Path(__file__).parents[2]
    / "character_creation_package"
    / "character_creation"
    / "data"
)


def test_content_packs_merge_and_validate():
    # Load base catalogs
    base_classes = classes_loader.load_class_catalog(DATA_ROOT / "classes.yaml")
    base_traits = traits_loader.load_trait_catalog(DATA_ROOT / "traits.yaml")
    base_races = races_loader.load_race_catalog(DATA_ROOT / "races.yaml")

    # Load packs config and merged overlay
    packs_cfg = load_packs_config(DATA_ROOT / "content_packs.yaml")
    merged_overlay = load_and_merge_enabled_packs(DATA_ROOT, packs_cfg)

    # Merge overlay into base copies
    policy = packs_cfg.get("merge", {}).get("on_conflict", "skip")
    base = {
        "classes": base_classes.get("classes", base_classes),
        "traits": base_traits.get("traits", base_traits),
        "races": base_races.get("races", base_races),
    }
    merged_all = merge_catalogs(base, merged_overlay, on_conflict=policy)

    # Assertions: lengths should grow or remain same
    assert len(merged_all.get("classes", [])) >= len(base.get("classes", []))
    assert len(merged_all.get("races", [])) >= len(base.get("races", []))
    assert len((merged_all.get("traits", {}) or {}).keys()) >= len(
        (base.get("traits", {}) or {}).keys()
    )

    # Appearance tables union sanity: if present, ensure at least one table includes all values
    if "appearance_tables" in merged_overlay:
        tables = merged_overlay["appearance_tables"]
        assert isinstance(tables, dict) and tables
        # Pick any one
        tname, pack_vals = next(iter(tables.items()))
        merged_vals = merged_all.get("appearance_tables", {}).get(tname, [])
        for v in pack_vals:
            assert v in merged_vals

    # Validate merged
    validate_merged_catalogs(merged_all)
