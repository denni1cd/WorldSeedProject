from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
import json
from character_creation.services.formula_eval import evaluate


@dataclass
class Character:
    name: str
    stats: Dict[str, float]
    stat_xp: Dict[str, float]
    classes: List[str] = field(default_factory=list)
    abilities: Set[str] = field(default_factory=set)
    traits: List[str] = field(default_factory=list)
    hp: float = 20.0
    mana: float = 20.0
    hp_max: float = 0.0
    mana_max: float = 0.0
    last_regen_time_hp: float = 0.0
    last_regen_time_mana: float = 0.0
    # Progression
    level: int = 1
    xp_total: float = 0.0
    stat_points: int = 0
    inventory: List[str] = field(default_factory=list)
    equipment: Dict[str, Optional[str]] = field(default_factory=dict)
    appearance: Dict[str, Any] = field(default_factory=dict)
    # Equipment bonuses
    equipped_stat_mods: Dict[str, float] = field(default_factory=dict)
    equipped_hp_bonus: float = 0.0
    equipped_mana_bonus: float = 0.0
    equipped_abilities: Set[str] = field(default_factory=set)
    active_effects: list[dict] = field(default_factory=list)

    def gain_xp(self, stat_key: str, amount: float, stat_template: Dict[str, dict]) -> None:
        xp_to_next = stat_template[stat_key].get("xp_to_next", 100)
        self.stat_xp[stat_key] = self.stat_xp.get(stat_key, 0.0) + amount
        while self.stat_xp[stat_key] >= xp_to_next:
            self.stat_xp[stat_key] -= xp_to_next
            self.increase_stat(stat_key, 0.1)

    def remove_xp(self, stat_key: str, amount: float) -> None:
        if stat_key in self.stat_xp:
            self.stat_xp[stat_key] = max(0.0, self.stat_xp[stat_key] - amount)

    def increase_stat(self, stat_key: str, amt: float) -> None:
        self.stats[stat_key] = self.stats.get(stat_key, 0.0) + amt

    def add_class(self, class_def: dict) -> None:
        class_id = class_def.get("id")
        if class_id and class_id not in self.classes:
            self.classes.append(class_id)
            for stat, val in class_def.get("grants_stats", {}).items():
                self.increase_stat(stat, val)
            abilities = class_def.get("grants_abilities", class_def.get("abilities", []))
            self.abilities.update(abilities)

    def remove_class(self, class_id: str) -> None:
        if class_id in self.classes:
            self.classes.remove(class_id)

    def add_traits(self, trait_ids: List[str]) -> None:
        for trait_id in trait_ids:
            if trait_id not in self.traits:
                self.traits.append(trait_id)

    def remove_traits(self, trait_ids: List[str]) -> None:
        for trait_id in trait_ids:
            if trait_id in self.traits:
                self.traits.remove(trait_id)

    def add_to_inventory(self, item_id: str) -> None:
        if item_id not in self.inventory:
            self.inventory.append(item_id)

    def remove_from_inventory(self, item_id: str) -> None:
        if item_id in self.inventory:
            self.inventory.remove(item_id)

    def equip(self, item_id: str, slot_id: str, items_catalog: Dict[str, Any]) -> None:
        if slot_id not in self.equipment:
            raise ValueError(f"Invalid slot_id: {slot_id}")
        # Remove the item from inventory if present (once)
        if item_id in self.inventory:
            self.inventory.remove(item_id)
        # Equip the item
        self.equipment[slot_id] = item_id
        # Recalculate bonuses
        self.recalc_equipment_bonuses(items_catalog)

    def add_ability(self, ability_id: str) -> None:
        self.abilities.add(ability_id)

    def remove_ability(self, ability_id: str) -> None:
        self.abilities.discard(ability_id)

    def change_stat(self, stat_key: str, new_value: float) -> None:
        self.stats[stat_key] = new_value

    def unequip(self, slot_id: str, items_catalog: Dict[str, Any]) -> None:
        if slot_id not in self.equipment:
            raise ValueError(f"Invalid slot_id: {slot_id}")
        if self.equipment.get(slot_id) is not None:
            item = self.equipment[slot_id]
            # Only append if not already present in inventory
            if item not in self.inventory:
                self.inventory.append(item)
            self.equipment[slot_id] = None
            # Recalculate bonuses
            self.recalc_equipment_bonuses(items_catalog)

    def recalc_equipment_bonuses(self, items_catalog: Dict[str, Any]) -> None:
        """
        Clear all equipped_* bonuses, then iterate self.equipment.values(),
        look up each item in items_catalog, and sum mods (stats/hp/mana/abilities).
        """
        self.equipped_stat_mods.clear()
        self.equipped_hp_bonus = 0.0
        self.equipped_mana_bonus = 0.0
        self.equipped_abilities.clear()
        for item_id in self.equipment.values():
            if not item_id:
                continue
            item = items_catalog.get(item_id)
            if not item:
                continue
            mods = item.get("mods", {})
            # Stats
            for stat, val in mods.get("stats", {}).items():
                self.equipped_stat_mods[stat] = self.equipped_stat_mods.get(stat, 0.0) + float(val)
            # HP
            if "hp" in mods:
                self.equipped_hp_bonus += float(mods["hp"])
            # Mana
            if "mana" in mods:
                self.equipped_mana_bonus += float(mods["mana"])
            # Abilities
            for ab in mods.get("abilities", []):
                self.equipped_abilities.add(ab)

    def get_effective_stat(self, stat_key: str) -> float:
        # Normalize stat key to match available keys (case-insensitive)
        stat_key_norm = stat_key.upper()
        # Try exact, then fallback to lower/upper
        stat_val = self.stats.get(stat_key_norm)
        if stat_val is None:
            # Try lower-case fallback
            stat_val = self.stats.get(stat_key_norm.lower(), 0.0)
        mod_val = self.equipped_stat_mods.get(stat_key_norm, 0.0)
        if mod_val == 0.0:
            mod_val = self.equipped_stat_mods.get(stat_key_norm.lower(), 0.0)
        return stat_val + mod_val

    def change_hp(self, new_value: float) -> None:
        self.hp = new_value

    def change_mana(self, new_value: float) -> None:
        self.mana = new_value

    def regen_tick(self, resource_config: dict, current_time: float) -> None:
        """
        Applies regeneration for HP and Mana if enough time has passed since last tick.
        Uses resource_config['regen_intervals'], ['regen_amounts'], and ['regen_caps'].
        """
        for res in ("hp", "mana"):
            interval = resource_config.get("regen_intervals", {}).get(res)
            amount = resource_config.get("regen_amounts", {}).get(res)
            cap = resource_config.get("regen_caps", {}).get(res)
            last_time_attr = f"last_regen_time_{res}"
            current_val = getattr(self, res)
            max_val = getattr(self, f"{res}_max", current_val)

            if interval is None or amount is None:
                continue

            last_time = getattr(self, last_time_attr)
            if current_time - last_time >= interval:
                ticks = int((current_time - last_time) // interval)
                current_val += amount * ticks
                if cap == "max":
                    current_val = min(current_val, max_val)
                elif isinstance(cap, (int, float)):
                    current_val = min(current_val, float(cap))
                setattr(self, res, current_val)
                setattr(self, last_time_attr, current_time)

    def apply_status_effect(self, effect_name: str, effect_data: dict, start_time: float) -> None:
        """Adds a status effect to active_effects with start time tracking."""
        self.active_effects.append(
            {
                "name": effect_name,
                "data": effect_data,
                "start_time": start_time,
                "last_tick": start_time,
            }
        )

    def update_status_effects(self, current_time: float) -> None:
        """Updates active effects, applies periodic damage or buffs, and removes expired ones."""
        remaining_effects = []
        for eff in self.active_effects:
            data = eff["data"]
            start_time = eff["start_time"]
            duration = data.get("duration", 0)
            expired = current_time - start_time > duration if duration > 0 else False

            if not expired:
                tick_interval = data.get("tick_interval")
                if tick_interval and current_time - eff["last_tick"] >= tick_interval:
                    if "tick_damage" in data:
                        self.hp -= data["tick_damage"]
                    if "modifies" in data:
                        for stat, mod in data["modifies"].items():
                            if isinstance(mod, (int, float)):
                                setattr(self, stat, getattr(self, stat) + mod)
                    eff["last_tick"] = current_time
                remaining_effects.append(eff)
        self.active_effects = remaining_effects

    def _value_for_context(self, v: Any) -> float:
        """
        Extract a numeric value from a stat representation for formula context.
        Supports objects with .current, dicts with 'current', or numeric values.
        """
        if hasattr(v, "current"):
            try:
                return float(v.current)
            except Exception:
                return 0.0
        if isinstance(v, dict):
            # Prefer 'current' then 'base'
            if "current" in v:
                try:
                    return float(v["current"])
                except Exception:
                    return 0.0
            if "base" in v:
                try:
                    return float(v["base"])
                except Exception:
                    return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            return 0.0

    def refresh_derived(
        self, formulas: dict, stat_template: dict, keep_percent: bool = True
    ) -> None:
        """
        Recompute HP/Mana bases from formulas['baseline']['hp'] and ['mana'] using formula_eval.evaluate.
        Context includes: 'level' + all stat keys as floats (self.stats).
        If keep_percent=True, preserve current% fill when changing base; else set current=base.
        """
        # Build evaluation context
        ctx: Dict[str, Any] = {"level": self.level}
        for s_name, s_val in self.stats.items():
            ctx[s_name] = self._value_for_context(s_val)

        # Compute new base values
        new_hp_base = float(evaluate(formulas["baseline"]["hp"], ctx))
        new_mana_base = float(evaluate(formulas["baseline"]["mana"], ctx))

        # Update HP structure
        hp_obj = self.stats.get("HP")
        if hasattr(hp_obj, "base") and hasattr(hp_obj, "current"):
            old_base = float(getattr(hp_obj, "base", new_hp_base)) or 1.0
            percent = float(getattr(hp_obj, "current", old_base)) / old_base if old_base else 1.0
            setattr(hp_obj, "base", new_hp_base)
            setattr(hp_obj, "current", percent * new_hp_base if keep_percent else new_hp_base)
        elif isinstance(hp_obj, dict) and ("base" in hp_obj or "current" in hp_obj):
            old_base = float(hp_obj.get("base", new_hp_base)) or 1.0
            percent = float(hp_obj.get("current", old_base)) / old_base if old_base else 1.0
            hp_obj["base"] = new_hp_base
            hp_obj["current"] = percent * new_hp_base if keep_percent else new_hp_base
        else:
            # Fall back to float attribute
            self.hp = new_hp_base
        # Update max values
        self.hp_max = new_hp_base

        # Update Mana structure
        mana_obj = self.stats.get("Mana")
        if hasattr(mana_obj, "base") and hasattr(mana_obj, "current"):
            old_base = float(getattr(mana_obj, "base", new_mana_base)) or 1.0
            percent = float(getattr(mana_obj, "current", old_base)) / old_base if old_base else 1.0
            setattr(mana_obj, "base", new_mana_base)
            setattr(mana_obj, "current", percent * new_mana_base if keep_percent else new_mana_base)
        elif isinstance(mana_obj, dict) and ("base" in mana_obj or "current" in mana_obj):
            old_base = float(mana_obj.get("base", new_mana_base)) or 1.0
            percent = float(mana_obj.get("current", old_base)) / old_base if old_base else 1.0
            mana_obj["base"] = new_mana_base
            mana_obj["current"] = percent * new_mana_base if keep_percent else new_mana_base
        else:
            # Fall back to float attribute
            self.mana = new_mana_base
        # Update max values
        self.mana_max = new_mana_base

    def xp_to_next_level(self, formulas: dict) -> float:
        """
        Compute xp needed for the NEXT level using formulas['baseline']['xp_to_next'], with context {'level': self.level}.
        """
        return float(evaluate(formulas["baseline"]["xp_to_next"], {"level": self.level}))

    def add_general_xp(
        self, amount: float, formulas: dict, stat_template: dict, progression: dict
    ) -> int:
        """
        Add XP; while xp_total >= xp_to_next(current level), level up:
          - level += 1
          - stat_points += progression.get('stat_points_per_level', 2)
          - if progression.auto_recalc_derived_on_level: call refresh_derived(..., keep_percent=progression.get('keep_current_percent_on_recalc', True))
        Return number of levels gained.
        """
        if amount <= 0:
            return 0

        self.xp_total += float(amount)
        levels_gained = 0
        stat_points_per_level = int(progression.get("stat_points_per_level", 2))
        auto_recalc = bool(progression.get("auto_recalc_derived_on_level", True))
        keep_percent = bool(progression.get("keep_current_percent_on_recalc", True))

        # Level-up loop (treat xp_total as per-level progress; subtract thresholds)
        while True:
            threshold = self.xp_to_next_level(formulas)
            if self.xp_total < threshold:
                break
            self.xp_total -= threshold
            self.level += 1
            self.stat_points += stat_points_per_level
            levels_gained += 1
            if auto_recalc:
                self.refresh_derived(
                    formulas=formulas, stat_template=stat_template, keep_percent=keep_percent
                )

        return levels_gained

    def spend_stat_points(self, allocations: Dict[str, float]) -> None:
        """
        allocations is a mapping like {'STR': 0.2, 'INT': 0.1}.
        Verify sum of positive deltas <= available stat_points * 0.1 granularity (or treat 1 point = +0.1).
        Default: 1 stat point == +0.1 to one stat.
        Deduct points and apply increases.
        Raise ValueError on overspend or unknown stats.
        """
        if not allocations:
            return

        # Validate
        EPS = 1e-9
        tenths_total = 0
        for stat_key, delta in allocations.items():
            if stat_key not in self.stats:
                raise ValueError(f"Unknown stat: {stat_key}")
            if delta < -EPS:
                raise ValueError("Negative allocations are not allowed")
            if delta < EPS:
                continue
            # Enforce 0.1 granularity
            tenths = round(delta * 10)
            if abs(delta * 10 - tenths) > 1e-6:
                raise ValueError("Allocations must be in 0.1 increments")
            tenths_total += tenths

        if tenths_total > self.stat_points:
            raise ValueError("Not enough stat points")

        # Apply
        for stat_key, delta in allocations.items():
            if delta <= 0:
                continue
            self.increase_stat(stat_key, float(delta))

        self.stat_points -= tenths_total

    def init_equipment_slots(self, slot_template: Dict[str, dict]) -> None:
        # Support nested slot templates (e.g., {"slots": {...}})
        def add_slots(template):
            for key, value in template.items():
                if isinstance(value, dict) and any(isinstance(v, dict) for v in value.values()):
                    add_slots(value)
                else:
                    self.equipment[key] = None

        add_slots(slot_template)

    def init_appearance(
        self, fields_spec: Dict[str, dict], defaults: Optional[Dict[str, Any]] = None
    ) -> None:
        defaults = defaults or {}
        for field_id, meta in fields_spec.items():
            self.appearance[field_id] = defaults.get(field_id, meta.get("default"))

    def to_json(self, path: str | Path) -> None:
        # Convert sets to lists for JSON serialization
        data = self.__dict__.copy()
        for k, v in data.items():
            if isinstance(v, set):
                data[k] = list(v)
        with open(str(path), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, path: str | Path) -> "Character":
        with open(str(path), "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert abilities back to set if loaded as list
        if isinstance(data.get("abilities"), list):
            data["abilities"] = set(data["abilities"])
        return cls(**data)
