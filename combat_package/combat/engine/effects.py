from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import ast

from .rng import RandomSource
from .combatant import Combatant

SAFE_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
SAFE_UNARY = (ast.UAdd, ast.USub)
SAFE_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Constant,
    ast.Name,
    ast.Load,
)


def _safe_eval(expr: str, ctx: Dict[str, float]) -> float:
    if not isinstance(expr, str):
        return float(expr)
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if not isinstance(node, SAFE_NODES):
            raise ValueError("Unsafe expression")
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):
            return float(node.n)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Bad const")
        if isinstance(node, ast.Name):
            return float(ctx.get(node.id, 0.0))
        if isinstance(node, ast.UnaryOp):
            v = _eval(node.operand)
            return +v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            a, b = _eval(node.left), _eval(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            elif isinstance(node.op, ast.Sub):
                return a - b
            elif isinstance(node.op, ast.Mult):
                return a * b
            elif isinstance(node.op, ast.Div):
                return a / b if b != 0 else 0.0
        raise ValueError("Unsupported")

    return float(_eval(tree))


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


@dataclass
class EffectInstance:
    id: str
    source_id: Optional[str]
    remaining: int
    stacks: int = 1


def _get_effect_def(effects_cfg: Dict[str, Any], eff_id: str) -> Dict[str, Any]:
    return (effects_cfg.get("effects") or {}).get(eff_id, {})


def apply_status(
    target: Combatant,
    eff_id: str,
    effects_cfg: Dict[str, Any],
    source_id: Optional[str] = None,
) -> EffectInstance | None:
    """
    Apply or update a status on target according to effect defs.
    - stack_mode: 'refresh' → set remaining to duration and cap stacks
                  'add'     → increment stacks up to max_stacks, duration stays at max(remaining, duration)
    """
    ed = _get_effect_def(effects_cfg, eff_id)
    if not ed:
        return None
    dur = int(ed.get("duration", 1))
    max_stacks = int(ed.get("max_stacks", 1))
    mode = str(ed.get("stack_mode", "refresh"))

    # find existing
    cur = next((s for s in target.statuses if s.get("id") == eff_id), None)
    if cur is None:
        inst = {"id": eff_id, "source_id": source_id, "remaining": dur, "stacks": 1}
        target.statuses.append(inst)
        return EffectInstance(**inst)
    # update
    if mode == "add":
        cur["stacks"] = min(max_stacks, int(cur.get("stacks", 1)) + 1)
        cur["remaining"] = max(int(cur.get("remaining", 1)), dur)
    else:  # refresh
        cur["stacks"] = min(max_stacks, int(cur.get("stacks", 1)))
        cur["remaining"] = dur
    return EffectInstance(**cur)


def apply_on_hit_effects(
    attacker: Combatant,
    target: Combatant,
    ability_def: Dict[str, Any],
    effects_cfg: Dict[str, Any],
    rng: RandomSource,
) -> List[EffectInstance]:
    """
    Ability may specify:
      on_hit:
        apply_status:
          - { id: burning, chance: 0.35 }
    """
    out: List[EffectInstance] = []
    oh = ability_def.get("on_hit") or {}
    applies = oh.get("apply_status") or []
    for spec in applies:
        eff_id = spec.get("id")
        if not eff_id:
            continue
        chance = float(spec.get("chance", 1.0))
        if rng.randf() <= _clamp01(chance):
            inst = apply_status(target, eff_id, effects_cfg, source_id=attacker.id)
            if inst:
                out.append(inst)
    return out


def tick_start_of_turn(
    actor: Combatant,
    effects_cfg: Dict[str, Any],
    rng: RandomSource,
) -> List[Dict[str, Any]]:
    """
    Apply per-tick damage for active statuses on actor at the start of their turn.
    Returns a list of events: {effect_id, dtype, amount}
    """
    events: List[Dict[str, Any]] = []
    if not actor.statuses:
        return events

    # Evaluate once per status (multiply by stacks)
    new_list: List[dict] = []
    for st in actor.statuses:
        ed = _get_effect_def(effects_cfg, st["id"])
        if not ed:
            continue
        stacks = int(st.get("stacks", 1))
        per_tick = str(ed.get("per_tick", "0"))
        dtype = str(ed.get("damage_type", ""))
        # context: use actor's own stats (harm scales with victim stats or with attacker's? we use victim INT here minimal; swap later easily)
        ctx = {
            "STR": float(actor.stats.get("STR", 0.0)),
            "DEX": float(actor.stats.get("DEX", 0.0)),
            "INT": float(actor.stats.get("INT", 0.0)),
            "STA": float(actor.stats.get("STA", 0.0)),
        }
        try:
            base = max(0.0, _safe_eval(per_tick, ctx))
        except Exception:
            base = 0.0
        # resistance (by effect dtype)
        res = float(actor.resist.get(dtype, 0.0)) if dtype else 0.0
        res = _clamp01(res)
        amt = round(base * stacks * (1.0 - res), 1)
        if amt > 0:
            actor.hp = max(0.0, actor.hp - amt)
            events.append(
                {"effect_id": st["id"], "dtype": dtype or "damage", "amount": amt}
            )

        # decrement duration
        rem = int(st.get("remaining", 1)) - 1
        if rem > 0:
            st["remaining"] = rem
            new_list.append(st)
        # else: expired → drop
    actor.statuses = new_list
    return events
