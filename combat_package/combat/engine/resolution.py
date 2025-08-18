from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import ast

from .rng import RandomSource
from .combatant import Combatant

SAFE_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)
SAFE_UNARY = (ast.UAdd, ast.USub)
SAFE_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load)


def _safe_eval(expr: str, ctx: Dict[str, float]) -> float:
    """
    Evaluate a tiny arithmetic expression safely:
    - names must come from ctx
    - supports + - * / and unary +/- only
    """
    if not isinstance(expr, str):
        return float(expr)
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if not isinstance(node, SAFE_NODES):
            raise ValueError("Unsafe expression")
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Const type")
        if isinstance(node, ast.Name):
            return float(ctx.get(node.id, 0.0))
        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, SAFE_UNARY):
                raise ValueError("Unary op")
            v = _eval(node.operand)
            return +v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, SAFE_BINOPS):
                raise ValueError("Bin op")
            a = _eval(node.left)
            b = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                return a / b if b != 0 else 0.0
        raise ValueError("Unsupported")

    return float(_eval(tree))


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class AttackResult:
    hit: bool
    crit: bool = False
    amount: float = 0.0
    dtype: str = "slashing"
    body_part: str = "chest"


def _format_amount(x: float) -> str:
    # pretty number for narration (avoid trailing .0)
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.1f}"


def _weighted_choice(weights: Dict[str, float], rng: RandomSource) -> str:
    # expects non-empty dict
    total = sum(max(0.0, float(w)) for w in weights.values()) or 0.0
    if total <= 0:
        # uniform fallback
        keys = list(weights.keys())
        return rng.choice(keys)
    r = rng.randf() * total
    acc = 0.0
    for k, w in weights.items():
        acc += max(0.0, float(w))
        if r <= acc:
            return k
    return next(iter(weights.keys()))


def _pick_body_part(
    groups: Dict[str, list],
    weights: Dict[str, Dict[str, float]],
    target: Combatant,
    rng: RandomSource,
) -> str:
    # try first matching tag, else 'humanoid', else any from groups
    group_key = None
    for t in target.tags:
        if t in groups:
            group_key = t
            break
    if group_key is None and "humanoid" in groups:
        group_key = "humanoid"
    if group_key is None and groups:
        group_key = next(iter(groups.keys()))
    parts = groups.get(group_key, [])
    if not parts:
        return "body"
    wmap = weights.get(group_key, {})
    # if weights missing, uniform
    if not wmap:
        return rng.choice(parts)
    # ensure weights only for available parts
    pruned = {k: wmap.get(k, 1.0) for k in parts}
    return _weighted_choice(pruned, rng)


def resolve_attack(
    attacker: Combatant,
    target: Combatant,
    ability_def: Dict[str, Any],
    body_parts: Dict[str, Any],
    rng: RandomSource,
) -> AttackResult:
    """
    Compute hit/crit/damage using safe data-driven formulas.
    - attacker/target stats are floats (missing default to 0)
    - resistances are 0..1 (clamped)
    """
    # context
    A = attacker.stats or {}
    T = target.stats or {}
    ctx = {
        "ATT": float(A.get("ATT", 0.0)),
        "DEX": float(A.get("DEX", 0.0)),
        "INT": float(A.get("INT", 0.0)),
        "STA": float(A.get("STA", 0.0)),
        "ARM": float(T.get("ARM", 0.0)),  # target armor in formula
        "WPN": float(A.get("WPN", 0.0)),  # weapon contribution
        # allow target dex in formulas with T_DEX if desired
        "T_DEX": float(T.get("DEX", 0.0)),
    }

    # hit chance (simple) - ensure reasonable hit chance for testing
    acc = _clamp(0.75 + (ctx["DEX"] - ctx["T_DEX"]) * 0.01, 0.15, 0.95)
    if rng.randf() > acc:
        return AttackResult(hit=False)

    # crit chance & mult
    crit_def = ability_def.get("crit") or {}
    crit_chance_expr = crit_def.get("chance", "0.05")
    crit_mult = float(crit_def.get("multiplier", 1.5))
    try:
        crit_chance = _clamp(_safe_eval(crit_chance_expr, ctx), 0.0, 1.0)
    except Exception:
        crit_chance = 0.05
    is_crit = rng.randf() < crit_chance

    # base damage
    formula = ability_def.get("formula", "ATT + WPN - ARM*0.6")
    try:
        base = max(0.0, _safe_eval(formula, ctx))
    except Exception:
        base = max(0.0, ctx["ATT"] + ctx["WPN"] - ctx["ARM"] * 0.6)
    if is_crit:
        base *= crit_mult

    dtype = str(ability_def.get("damage_type", "slashing"))
    res = float(target.resist.get(dtype, 0.0))
    res = _clamp(res, 0.0, 0.95)
    amt = round(base * (1.0 - res), 1)

    groups = body_parts.get("groups", {})
    weights = body_parts.get("weights", {})
    part = _pick_body_part(groups, weights, target, rng)

    return AttackResult(hit=True, crit=is_crit, amount=amt, dtype=dtype, body_part=part)
