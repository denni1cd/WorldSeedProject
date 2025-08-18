from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Combatant:
    id: str
    name: str
    stats: Dict[str, float]  # e.g., {"STR":8, "DEX":7, "INT":5, "ARM":2, "WPN":3}
    hp: float
    mana: float
    resist: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)  # e.g., ["humanoid"]

    def is_alive(self) -> bool:
        return self.hp > 0
