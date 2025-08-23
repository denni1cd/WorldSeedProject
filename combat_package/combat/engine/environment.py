from __future__ import annotations
from typing import Dict, Any, List
from .combatant import Combatant
from .rng import RandomSource
import ast


def _safe_eval(expr: str, ctx: Dict[str, float]) -> float:
    if not isinstance(expr, str):
        return float(expr)
    tree = ast.parse(expr, mode="eval")
    SAFE = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.UAdd,
        ast.USub,
    )

    def ev(n):
        if type(n) not in SAFE:
            raise ValueError("Unsafe")
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return float(n.value)
            raise ValueError("bad const")
        if isinstance(n, ast.Name):
            return float(ctx.get(n.id, 0.0))
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            return +v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b if b != 0 else 0.0
        raise ValueError("Unsupported")

    return float(ev(tree))


def _choice_weighted(rng: RandomSource, lines: List[dict]) -> str:
    if not lines:
        return ""
    pool = []
    for ln in lines:
        w = int(ln.get("weight", 1) or 1)
        pool.extend([ln.get("text", "")] * max(1, w))
    return rng.choice(pool)


class Environment:
    """
    Applies hazard effects at configured phases.
    Keeps per-hazard remaining duration (rounds) if > 0.
    """

    def __init__(self, hazards_cfg: Dict[str, Any]):
        self.hazards = []
        for h in hazards_cfg.get("hazards") or []:
            h = dict(h)
            dur = int(h.get("duration_rounds", 0) or 0)
            h["_remaining_rounds"] = dur
            self.hazards.append(h)

    def tick_round_boundary(self) -> None:
        """Call at start_of_round to decrement round-based durations AFTER the first round."""
        # We'll decrement at the *end* of a full round in Encounter; for simplicity, leave here no-op.
        pass

    def process_phase(
        self,
        phase: str,
        participants: List[Combatant],
        rng: RandomSource,
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of typed events for narration/logging:
          {"type":"hazard","hazard_id":..., "target_id":..., "kind":"damage|heal|resource|effect", "amount":float, "dtype":str|None}
        """
        events: List[Dict[str, Any]] = []
        for hz in list(self.hazards):
            if hz.get("phase") != phase:
                continue
            # duration check: 0 = persistent; if >0 and exhausted, skip
            if int(hz.get("_remaining_rounds", 0)) == 0 and int(hz.get("duration_rounds", 0)) > 0:
                continue
            t = hz.get("targeting") or {}
            locs = set(t.get("locations") or [])
            team = str(t.get("team", "any"))
            absent = set(t.get("require_tag_absent") or [])
            # candidates
            cands = [c for c in participants if c.is_alive()]
            if locs:
                cands = [c for c in cands if c.location in locs]
            if team != "any":
                cands = [c for c in cands if c.team == team]
            if absent:
                cands = [c for c in cands if not any(tag in absent for tag in (c.tags or []))]

            eff = hz.get("effects") or {}
            for c in cands:
                # context: victim stats for scaling (safe)
                ctx = {
                    "STR": float(c.stats.get("STR", 0.0)),
                    "DEX": float(c.stats.get("DEX", 0.0)),
                    "INT": float(c.stats.get("INT", 0.0)),
                    "STA": float(c.stats.get("STA", 0.0)),
                }
                # damage
                if "damage" in eff:
                    spec = eff["damage"] or {}
                    amt = spec.get("amount", 0)
                    try:
                        val = max(0.0, _safe_eval(amt, ctx))
                    except Exception:
                        val = 0.0
                    dtype = spec.get("damage_type")
                    # apply resist
                    res = float(c.resist.get(dtype, 0.0)) if dtype else 0.0
                    val = round(val * (1.0 - max(0.0, min(1.0, res))), 1)
                    if val > 0:
                        c.hp = max(0.0, c.hp - val)
                        events.append(
                            {
                                "type": "hazard",
                                "hazard_id": hz.get("id"),
                                "target_id": c.id,
                                "kind": "damage",
                                "amount": val,
                                "dtype": dtype,
                            }
                        )
                # heal
                if "heal" in eff:
                    h = float(eff["heal"].get("amount", 0))
                    if h > 0:
                        c.hp = c.hp + h
                        events.append(
                            {
                                "type": "hazard",
                                "hazard_id": hz.get("id"),
                                "target_id": c.id,
                                "kind": "heal",
                                "amount": h,
                                "dtype": None,
                            }
                        )
                # resource (mana only for now)
                if "resource" in eff:
                    mp = float((eff["resource"] or {}).get("mana", 0))
                    if mp > 0:
                        c.mana = c.mana + mp
                        events.append(
                            {
                                "type": "hazard",
                                "hazard_id": hz.get("id"),
                                "target_id": c.id,
                                "kind": "resource",
                                "amount": mp,
                                "dtype": None,
                            }
                        )
                # apply_status
                for spec in eff.get("apply_status") or []:
                    from .effects import apply_status

                    eid = spec.get("id")
                    chance = float(spec.get("chance", 1.0))
                    if eid and rng.randf() <= chance:
                        inst = apply_status(
                            c, eid, {"effects": {}}, source_id=f"hazard:{hz.get('id')}"
                        )
                        if inst:
                            events.append(
                                {
                                    "type": "hazard",
                                    "hazard_id": hz.get("id"),
                                    "target_id": c.id,
                                    "kind": "effect",
                                    "effect_id": eid,
                                    "amount": 0.0,
                                    "dtype": None,
                                }
                            )
            # duration bookkeeping for finite hazards: decrement per round at end_of_turn of last unit if needed (handled by Encounter)
        return events
