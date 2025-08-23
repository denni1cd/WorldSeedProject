from __future__ import annotations
from typing import List, Dict, Any, Optional
from .combatant import Combatant
from .rng import RandomSource
from .threat import blank_table, add_threat, normalize


def _dex_of(c: Combatant) -> float:
    try:
        return float(c.stats.get("DEX", 0.0) or 0.0)
    except Exception:
        return 0.0


class Encounter:
    def __init__(self, participants: List[Combatant], seed: int | None = 1234):
        if not participants:
            raise ValueError("Encounter requires at least one participant.")
        self.participants = list(participants)
        self.rng = RandomSource(seed)
        self.threat = blank_table([c.id for c in self.participants])
        self._order = sorted(
            range(len(self.participants)),
            key=lambda i: (
                -_dex_of(self.participants[i]),
                self.participants[i].name.lower(),
                self.participants[i].id,
            ),
        )
        self._ptr = 0
        self._round = 1
        self.log: List[str] = []
        self.events: List[Dict[str, Any]] = []  # typed event log

    @property
    def order_ids(self) -> List[str]:
        return [self.participants[i].id for i in self._order]

    def next_turn(self) -> Combatant:
        idx = self._order[self._ptr]
        self._ptr = (self._ptr + 1) % len(self._order)
        if self._ptr == 0:
            self._round += 1
        return self.participants[idx]

    def living(self, team: Optional[str] = None) -> List[Combatant]:
        units = [c for c in self.participants if c.is_alive()]
        return [u for u in units if (team is None or u.team == team)]

    # Existing helper:
    def tick_cooldowns(self, actor: Combatant) -> None:
        if not actor.cooldowns:
            return
        for k in list(actor.cooldowns.keys()):
            actor.cooldowns[k] = max(0, int(actor.cooldowns.get(k, 0)) - 1)

    # NEW: snapshot/restore (deterministic)
    def snapshot(self) -> Dict[str, Any]:
        return {
            "rng_state": self.rng.get_state(),
            "order": list(self._order),
            "ptr": int(self._ptr),
            "round": int(self._round),
            "participants": [
                {
                    "id": c.id,
                    "name": c.name,
                    "team": c.team,
                    "stats": dict(c.stats),
                    "hp": float(c.hp),
                    "mana": float(c.mana),
                    "resist": dict(c.resist),
                    "tags": list(c.tags),
                    "statuses": [dict(s) for s in (c.statuses or [])],
                    "cooldowns": dict(c.cooldowns),
                }
                for c in self.participants
            ],
        }

    def restore(self, snap: Dict[str, Any]) -> None:
        self.rng.set_state(snap["rng_state"])
        self._order = list(snap["order"])
        self._ptr = int(snap["ptr"])
        self._round = int(snap["round"])
        by_id = {c.id: c for c in self.participants}
        for sd in snap["participants"]:
            c = by_id.get(sd["id"])
            if not c:
                continue
            c.name = sd["name"]
            c.team = sd["team"]
            c.stats = dict(sd["stats"])
            c.hp = float(sd["hp"])
            c.mana = float(sd["mana"])
            c.resist = dict(sd["resist"])
            c.tags = list(sd["tags"])
            c.statuses = [dict(s) for s in (sd.get("statuses") or [])]
            c.cooldowns = dict(sd.get("cooldowns") or {})

    # OPTIONAL convenience for automation: run until end or N rounds
    def run_until(self, max_rounds: int = 50) -> Dict[str, Any]:
        """
        Minimal auto-sim: each unit attacks the first living enemy with 'basic_attack'.
        Returns {ended: bool, winner_team: str|None}
        """
        from .abilities import execute_ability
        from ..loaders.narration_loader import load_narration
        from ..loaders.body_parts_loader import load_body_parts
        from pathlib import Path

        # Load required configs for the auto-sim
        load_body_parts(Path(__file__).parents[1] / "data" / "body_parts.yaml")
        load_narration(Path(__file__).parents[1] / "data" / "narration.yaml")
        import yaml

        abilities = (
            yaml.safe_load(
                open(
                    Path(__file__).parents[1] / "data" / "abilities.yaml",
                    "r",
                    encoding="utf-8",
                )
            )
            or {}
        )
        basic = next(
            (x for x in abilities.get("abilities", []) if x.get("id") == "basic_attack"),
            {
                "id": "basic_attack",
                "formula": "ATT + WPN - ARM*0.6",
                "damage_type": "slashing",
                "targeting": "single_enemy",
            },
        )

        while self._round <= max_rounds and len({c.team for c in self.living()}) > 1:
            actor = self.next_turn()
            if not actor.is_alive():
                continue
            # tick phase
            from .effects import tick_start_of_turn

            self.tick_cooldowns(actor)
            dot_events = tick_start_of_turn(
                actor, {"effects": {}}, self.rng
            )  # cfg injected by CLI/tests; here use empty to avoid IO
            for ev in dot_events:
                self.events.append(
                    {
                        "type": "dot",
                        "target_id": actor.id,
                        "effect_id": ev["effect_id"],
                        "amount": ev["amount"],
                    }
                )
            # choose first enemy
            enemies = [c for c in self.living() if c.team != actor.team]
            if not enemies:
                break
            tgt = enemies[0]
            res = execute_ability(self.participants, actor, basic, [tgt.id], self.rng)
            self.events.extend(res.events or [])
            if len({c.team for c in self.living()}) <= 1:
                break
        teams_alive = {c.team for c in self.living()}
        return {
            "ended": len(teams_alive) <= 1,
            "winner_team": next(iter(teams_alive)) if len(teams_alive) == 1 else None,
        }

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

    def ingest_events_update_threat(self, events: List[Dict[str, Any]]) -> None:
        """
        For each 'hit' event, increase threat on the VICTIM toward the ATTACKER by damage amount (+bonus if crit).
        For 'effect' of type 'taunted' we don't adjust threat (taunt already collapses targeting).
        """
        for ev in events or []:
            if ev.get("type") == "hit":
                victim = ev.get("target_id")
                attacker = ev.get("actor_id")
                amt = float(ev.get("amount", 0.0))
                if ev.get("crit"):
                    amt *= 1.25
                if victim and attacker:
                    add_threat(self.threat, victim, attacker, amt)
        normalize(self.threat)
