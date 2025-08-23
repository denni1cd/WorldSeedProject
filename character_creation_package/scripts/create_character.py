from pathlib import Path
from character_creation.loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    races_loader,
)
from character_creation.loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)
from character_creation.ui.cli.wizard import run_wizard, confirm_save_path
from character_creation.loaders import difficulty_loader
from character_creation.services.balance import current_profile


def main() -> None:
    root = Path(__file__).parents[1]
    # Resolve data paths
    stats_path = root / "character_creation" / "data" / "stats" / "stats.yaml"
    classes_path = root / "character_creation" / "data" / "classes.yaml"
    traits_path = root / "character_creation" / "data" / "traits.yaml"
    races_path = root / "character_creation" / "data" / "races.yaml"
    slots_path = root / "character_creation" / "data" / "slots.yaml"
    fields_path = root / "character_creation" / "data" / "appearance" / "fields.yaml"
    defaults_path = root / "character_creation" / "data" / "appearance" / "defaults.yaml"
    resources_path = root / "character_creation" / "data" / "resources.yaml"

    # Load YAML data
    stat_tmpl = stats_loader.load_stat_template(stats_path)
    class_catalog = classes_loader.load_class_catalog(classes_path)
    trait_catalog = traits_loader.load_trait_catalog(traits_path)
    race_catalog = races_loader.load_race_catalog(races_path)
    slot_tmpl = slots_loader.load_slot_template(slots_path)
    fields = appearance_loader.load_appearance_fields(fields_path)
    defaults = appearance_loader.load_appearance_defaults(defaults_path)
    resources = resources_loader.load_resources(resources_path)
    # Formulas
    formulas_path = root / "character_creation" / "data" / "formulas.yaml"
    try:
        import yaml  # noqa: PLC0415

        formulas = yaml.safe_load(open(formulas_path, "r", encoding="utf-8"))
    except Exception:
        formulas = {}
    # Difficulty config
    difficulty_path = root / "character_creation" / "data" / "difficulty.yaml"
    balance_cfg = difficulty_loader.load_difficulty(difficulty_path)
    balance_prof = current_profile(balance_cfg)

    # Load content packs config and merged overlays (tolerate absence)
    packs_cfg_path = root / "character_creation" / "data" / "content_packs.yaml"
    packs_cfg = load_packs_config(packs_cfg_path)
    merged_overlay = load_and_merge_enabled_packs(
        base_root=root / "character_creation" / "data", packs_cfg=packs_cfg
    )

    # Apply merges to catalogs
    if merged_overlay:
        policy = packs_cfg.get("merge", {}).get("on_conflict", "skip")
        base = {
            "classes": class_catalog.get("classes", class_catalog),
            "traits": trait_catalog.get("traits", trait_catalog),
            "races": race_catalog.get("races", race_catalog),
        }
        # Items are optional to CLI run; only pass when needed elsewhere
        merged_all = merge_catalogs(base, merged_overlay, on_conflict=policy)
        if "classes" in merged_all:
            class_catalog = {"classes": merged_all["classes"]}
        if "traits" in merged_all:
            trait_catalog = {"traits": merged_all["traits"]}
        if "races" in merged_all:
            race_catalog = {"races": merged_all["races"]}
        # For appearance tables, we hook via services.appearance_logic where needed by passing extras
        # CLI wizard directly calls get_enum_values; to avoid larger refactor, we will attach
        # the merged tables onto the fields dict under a private key consumed by get_enum_values.
        if "appearance_tables" in merged_overlay and isinstance(fields, dict):
            fields = dict(fields)
            fields["_extra_appearance_tables"] = merged_overlay["appearance_tables"]

    # Run wizard
    hero = run_wizard(
        {
            "stat_tmpl": stat_tmpl,
            "slot_tmpl": slot_tmpl,
            "appearance_fields": fields,
            "appearance_defaults": defaults,
            "resources": resources,
            "class_catalog": class_catalog,
            "trait_catalog": trait_catalog,
            "race_catalog": race_catalog,
            "balance_cfg": balance_cfg,
            "balance_profile": balance_prof,
        }
    )

    # Set difficulty label and recompute derived with chosen balance
    try:
        hero.difficulty = str(balance_cfg.get("current", "normal"))
        # Recompute derived with balance scaling applied
        hero.refresh_derived(
            formulas=formulas,
            stat_template=stat_tmpl,
            keep_percent=False,
            balance=balance_prof,
        )
    except Exception:
        pass

    # Ask for save path
    default_path = str(root / "hero.json")
    save_path = confirm_save_path(default_path)
    hero.to_json(save_path)
    print(f"Character saved to {save_path}")


if __name__ == "__main__":
    main()
