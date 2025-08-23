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

    def tick_cooldowns(self, actor: Combatant) -> None:
        if not actor.cooldowns:
            return
        for k in list(actor.cooldowns.keys()):
            actor.cooldowns[k] = max(0, int(actor.cooldowns.get(k, 0)) - 1)
            if actor.cooldowns[k] == 0:
                # keep key with 0 so UI can show ready state; or remove if preferred
                pass

    def run_round(self) -> dict:
        """
        Very small demo round:
        - first actor attacks the next living opponent
        - then next actor (if alive) retaliates
        - appends narration strings to self.log
        Returns: {"ended": bool, "winner": id|None}
        """
        from .resolution import resolve_attack
        from .narration import render_event
        from ..loaders.abilities_loader import load_abilities
        from ..loaders.body_parts_loader import load_body_parts
        from ..loaders.narration_loader import load_narration
        from pathlib import Path

        alive = [c for c in self.participants if c.is_alive()]
        if len(alive) <= 1:
            return {"ended": True, "winner": alive[0].id if alive else None}

        data_root = Path(__file__).parents[2] / "data"
        abilities = load_abilities(data_root / "abilities.yaml")
        ability = {}
        for a in abilities.get("abilities", []):
            if a.get("id") == "basic_attack":
                ability = a
                break
        if not ability:
            ability = {
                "id": "basic_attack",
                "formula": "ATT + WPN - ARM*0.6",
                "damage_type": "slashing",
                "crit": {"chance": "0.05", "multiplier": 1.5},
            }

        body_parts = load_body_parts(data_root / "body_parts.yaml")
        narration_cfg = load_narration(data_root / "narration.yaml")

        # two actors in order
        a1 = self.next_turn()
        # pick target = first living not self
        targets = [c for c in self.participants if c.id != a1.id and c.is_alive()]
        if not targets:
            return {"ended": True, "winner": a1.id}
        t1 = targets[0]

        r1 = resolve_attack(a1, t1, ability, body_parts, self.rng)
        if r1.hit:
            t1.hp = max(0.0, t1.hp - r1.amount)
        line1 = render_event(
            {
                "actor": a1.name,
                "target": t1.name,
                "hit": r1.hit,
                "crit": r1.crit,
                "amount": r1.amount,
                "dtype": r1.dtype,
                "body_part": r1.body_part,
            },
            narration_cfg,
            self.rng,
        )
        self.log.append(line1)

        # second actor (if still alive)
        if not t1.is_alive():
            return {"ended": True, "winner": a1.id}

        a2 = t1
        t2_candidates = [c for c in self.participants if c.id != a2.id and c.is_alive()]
        if not t2_candidates:
            return {"ended": True, "winner": a2.id}
        t2 = t2_candidates[0]
        r2 = resolve_attack(a2, t2, ability, body_parts, self.rng)
        if r2.hit:
            t2.hp = max(0.0, t2.hp - r2.amount)
        line2 = render_event(
            {
                "actor": a2.name,
                "target": t2.name,
                "hit": r2.hit,
                "crit": r2.crit,
                "amount": r2.amount,
                "dtype": r2.dtype,
                "body_part": r2.body_part,
            },
            narration_cfg,
            self.rng,
        )
        self.log.append(line2)

        alive = [c for c in self.participants if c.is_alive()]
        return {
            "ended": len(alive) <= 1,
            "winner": alive[0].id if len(alive) == 1 else None,
        }
