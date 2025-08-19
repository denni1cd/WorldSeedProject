from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Callable
import time

import yaml

try:
    from watchfiles import watch

    WATCHFILES_AVAILABLE = True
except ImportError:
    WATCHFILES_AVAILABLE = False

from ..loaders import (
    stats_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    classes_loader,
    traits_loader,
    items_loader,
    races_loader,
)
from ..loaders import content_packs_loader
from .validate_data import (
    validate_stats,
    validate_classes,
    validate_traits,
    validate_slots,
    validate_items,
    validate_races,
    validate_appearance_fields,
    validate_appearance_table,
    validate_numeric_range,
    validate_creation_limits,
    validate_merged_catalogs,
)


class CatalogReloader:
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        # Be robust to different working directories: if provided path doesn't contain
        # expected files (e.g., stats/stats.yaml), fall back to the package data dir.
        try:
            expected = self.data_root / "stats" / "stats.yaml"
            if not expected.exists():
                pkg_data = Path(__file__).parents[1] / "data"
                if (pkg_data / "stats" / "stats.yaml").exists():
                    self.data_root = pkg_data
        except Exception:
            pass
        self.version = 0
        self._last_ok: Dict[str, Any] | None = None

    def _load_base(self) -> Dict[str, Any]:
        dr = self.data_root
        stats = stats_loader.load_stat_template(dr / "stats" / "stats.yaml")
        slots = slots_loader.load_slot_template(dr / "slots.yaml")
        fields = appearance_loader.load_appearance_fields(
            dr / "appearance" / "fields.yaml"
        )
        defaults = appearance_loader.load_appearance_defaults(
            dr / "appearance" / "defaults.yaml"
        )
        resources = resources_loader.load_resources(dr / "resources.yaml")
        classes = classes_loader.load_class_catalog(dr / "classes.yaml")
        traits = traits_loader.load_trait_catalog(dr / "traits.yaml")
        items = items_loader.load_item_catalog(dr / "items.yaml")
        races = races_loader.load_race_catalog(dr / "races.yaml")
        progression = progression_loader.load_progression(dr / "progression.yaml")
        with open(dr / "formulas.yaml", "r", encoding="utf-8") as f:
            formulas = yaml.safe_load(f)
        limits_path = dr / "creation_limits.yaml"
        if limits_path.exists():
            with open(limits_path, "r", encoding="utf-8") as f:
                creation_limits = yaml.safe_load(f) or {}
        else:
            creation_limits = {}

        # Optional content packs
        packs_cfg_path = dr / "content_packs.yaml"
        if packs_cfg_path.exists():
            with open(packs_cfg_path, "r", encoding="utf-8") as f:
                packs_cfg = yaml.safe_load(f) or {
                    "enabled": [],
                    "merge": {"on_conflict": "skip"},
                }
        else:
            packs_cfg = {"enabled": [], "merge": {"on_conflict": "skip"}}
        merged_from_packs = content_packs_loader.load_and_merge_enabled_packs(
            dr, packs_cfg
        )

        # Merge helper
        def list_merge(base_list, add_list, key="id"):
            if not isinstance(base_list, list):
                base_list = []
            seen = {x.get(key) for x in base_list if isinstance(x, dict)}
            for it in add_list or []:
                if isinstance(it, dict) and it.get(key) not in seen:
                    base_list.append(it)
                    seen.add(it.get(key))
            return base_list

        # Normalize loaders that may return list-only or dict wrappers
        def ensure_dict_list(wrapper_key: str, data_obj: Any) -> Dict[str, Any]:
            if isinstance(data_obj, dict) and wrapper_key in data_obj:
                return {wrapper_key: list(data_obj[wrapper_key])}
            if isinstance(data_obj, list):
                return {wrapper_key: list(data_obj)}
            return {wrapper_key: []}

        classes = ensure_dict_list("classes", classes)
        races = ensure_dict_list("races", races)
        # traits should be mapping under 'traits'
        if isinstance(traits, dict) and "traits" in traits:
            traits = {"traits": dict(traits["traits"])}
        elif isinstance(traits, dict):
            traits = {"traits": dict(traits)}
        else:
            traits = {"traits": {}}
        # items should be list under 'items'
        if isinstance(items, dict) and "items" in items:
            items = {
                "items": (
                    list(items["items"])
                    if isinstance(items["items"], list)
                    else list(items.values())
                )
            }
        elif isinstance(items, list):
            items = {"items": list(items)}
        else:
            items = {"items": []}

        # Apply merged overlays
        if "classes" in merged_from_packs:
            classes = {
                "classes": list_merge(
                    classes.get("classes", []), merged_from_packs["classes"]
                )
            }
        if "traits" in merged_from_packs:
            merged_traits = dict(traits.get("traits", {}))
            merged_traits.update(merged_from_packs["traits"])
            traits = {"traits": merged_traits}
        if "races" in merged_from_packs:
            races = {
                "races": list_merge(races.get("races", []), merged_from_packs["races"])
            }
        if "items" in merged_from_packs:
            items = {
                "items": list_merge(items.get("items", []), merged_from_packs["items"])
            }

        # Appearance tables union (base + packs)
        appearance_tables: Dict[str, Any] = {}
        tables_dir = dr / "appearance" / "tables"
        if tables_dir.exists():
            for p in tables_dir.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or []
                if isinstance(loaded, dict) and "values" in loaded:
                    values = loaded.get("values") or []
                elif isinstance(loaded, list):
                    values = loaded
                else:
                    values = []
                appearance_tables[p.stem] = values
        if "appearance_tables" in merged_from_packs:
            for k, vals in merged_from_packs["appearance_tables"].items():
                base_vals = list(appearance_tables.get(k, []))
                for v in vals or []:
                    if v not in base_vals:
                        base_vals.append(v)
                appearance_tables[k] = base_vals

        return {
            "stats": stats,
            "slots": slots,
            "appearance_fields": fields,
            "appearance_defaults": defaults,
            "resources": resources,
            "class_catalog": classes,
            "trait_catalog": traits,
            "items_catalog": items,
            "race_catalog": races,
            "appearance_tables": appearance_tables,
            "progression": progression,
            "formulas": formulas,
            "creation_limits": creation_limits,
        }

    def _validate_all(self, cats: Dict[str, Any]) -> None:
        validate_stats(cats["stats"])
        validate_classes(cats["class_catalog"])
        validate_traits(cats["trait_catalog"])
        validate_slots(cats["slots"])
        validate_items(cats["items_catalog"], cats["slots"])
        validate_races(cats["race_catalog"])
        validate_appearance_fields(cats["appearance_fields"])
        # Validate one table and one range if present
        dr = self.data_root
        tables_dir = dr / "appearance" / "tables"
        ranges_dir = dr / "appearance" / "ranges"
        if tables_dir.exists():
            for p in tables_dir.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    validate_appearance_table(yaml.safe_load(f), p.stem)
                break
        if ranges_dir.exists():
            for p in ranges_dir.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    validate_numeric_range(yaml.safe_load(f), p.stem)
                break
        validate_creation_limits(cats.get("creation_limits", {}))
        validate_merged_catalogs(
            {
                "classes": cats["class_catalog"].get("classes", []),
                "traits": cats["trait_catalog"].get("traits", {}),
                "races": cats["race_catalog"].get("races", []),
                "items": cats["items_catalog"].get("items", []),
                "appearance_tables": cats["appearance_tables"],
            }
        )

    def reload_once(self) -> Dict[str, Any]:
        cats = self._load_base()
        self._validate_all(cats)
        self.version += 1
        self._last_ok = cats
        return cats

    def watch(
        self,
        callback: Callable[[Dict[str, Any], int, list], None],
        debounce_ms: int = 300,
    ) -> None:
        if not WATCHFILES_AVAILABLE:
            raise ImportError(
                "watchfiles is not installed. Install it with: pip install watchfiles"
            )

        data_dir = str(self.data_root)
        last_emit = 0.0
        for changes in watch(data_dir, recursive=True):
            now = time.time()
            if (now - last_emit) * 1000 < debounce_ms:
                continue
            last_emit = now
            try:
                cats = self.reload_once()
                callback(cats, self.version, list(changes))
            except Exception as e:  # noqa: BLE001
                print(f"[LiveReload] Validation error: {e}")
