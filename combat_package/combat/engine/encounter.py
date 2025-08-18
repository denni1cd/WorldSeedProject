from __future__ import annotations
from typing import List
from .combatant import Combatant
from .rng import RandomSource


def _dex_of(c: Combatant) -> float:
    try:
        v = c.stats.get("DEX", 0.0)
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


class Encounter:
    """Holds participants, initiative order, and a simple turn pointer."""

    def __init__(self, participants: List[Combatant], seed: int | None = 1234):
        if not participants:
            raise ValueError("Encounter requires at least one participant.")
        self.participants = list(participants)
        self.rng = RandomSource(seed)
        # Sort by DEX desc, then name asc, then id asc for stability
        self._order = sorted(
            range(len(self.participants)),
            key=lambda i: (
                -_dex_of(self.participants[i]),
                self.participants[i].name.lower(),
                self.participants[i].id,
            ),
        )
        self._ptr = 0
        self.log: List[str] = []

    @property
    def order_ids(self) -> List[str]:
        return [self.participants[i].id for i in self._order]

    def next_turn(self) -> Combatant:
        """Return the next actor in cyclic order."""
        idx = self._order[self._ptr]
        self._ptr = (self._ptr + 1) % len(self._order)
        return self.participants[idx]
