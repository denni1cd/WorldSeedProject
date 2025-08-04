from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
import json


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
    inventory: List[str] = field(default_factory=list)
    equipment: Dict[str, Optional[str]] = field(default_factory=dict)
    appearance: Dict[str, Any] = field(default_factory=dict)
    # Equipment bonuses
    equipped_stat_mods: Dict[str, float] = field(default_factory=dict)
    equipped_hp_bonus: float = 0.0
    equipped_mana_bonus: float = 0.0
    equipped_abilities: Set[str] = field(default_factory=set)

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
        if slot_id in self.equipment:
            self.equipment[slot_id] = item_id
            self.recalc_equipment_bonuses(items_catalog)

    def add_ability(self, ability_id: str) -> None:
        self.abilities.add(ability_id)

    def remove_ability(self, ability_id: str) -> None:
        self.abilities.discard(ability_id)

    def change_stat(self, stat_key: str, new_value: float) -> None:
        self.stats[stat_key] = new_value

    def unequip(self, slot_id: str, items_catalog: Dict[str, Any]) -> None:
        if slot_id in self.equipment and self.equipment[slot_id] is not None:
            item = self.equipment[slot_id]
            self.inventory.append(item)
            self.equipment[slot_id] = None
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
