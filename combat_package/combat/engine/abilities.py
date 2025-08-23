from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from .combatant import Combatant
from .rng import RandomSource
from .resolution import resolve_attack
from .effects import apply_on_hit_effects
from ..loaders.body_parts_loader import load_body_parts
from pathlib import Path


@dataclass
class AbilityUseResult:
    ok: bool
    reason: str = ""
    events: List[Dict[str, Any]] = None  # list of {"type": "hit"|"miss"|"effect", ...}


def _get_resource(c: Combatant, name: str) -> float:
    if name == "mana":
        return float(c.mana)
    # room for other resources later (stamina, focus...)
    return 0.0


def _spend_resource(c: Combatant, name: str, amount: float) -> None:
    if name == "mana":
        c.mana = max(0.0, float(c.mana) - float(amount))
    # extend when new resources appear


def _targets_by_spec(enc_participants: List[Combatant], actor: Combatant, spec: str) -> List[str]:
    # For now we support only "single_enemy" and "self".
    if spec == "self":
        return [actor.id]
    # enemies = anyone not actor; allies are not implemented yet
    return [c.id for c in enc_participants if c.id != actor.id and c.is_alive()]


def can_use_ability(
    actor: Combatant,
    ability_def: Dict[str, Any],
) -> Tuple[bool, str]:
    # cooldown gate
    cd = int(ability_def.get("cooldown", 0) or 0)
    if cd > 0 and actor.cooldowns.get(ability_def.get("id", ""), 0) > 0:
        return False, "on_cooldown"

    # resource gate
    costs = ability_def.get("resource_cost") or {}
    for k, v in costs.items():
        need = float(v)
        have = _get_resource(actor, k)
        if have + 1e-9 < need:
            return False, f"insufficient_{k}"

    return True, ""


def execute_ability(
    participants: List[Combatant],
    actor: Combatant,
    ability_def: Dict[str, Any],
    target_ids: List[str],
    rng: RandomSource,
) -> AbilityUseResult:
    """
    Executes the ability (attack style only, for now).
    Validates targets against ability.targeting.
    Deducts resources and sets cooldown only if execution proceeds.
    Returns events:
      - hit/miss entries: {"type":"hit","target_id":...,"amount":...,"dtype":...,"crit":bool,"body_part":...}
      - effect entries:   {"type":"effect","target_id":...,"effect_id":...}
    """
    evs: List[Dict[str, Any]] = []
    # validate targeting
    targeting = str(ability_def.get("targeting", "single_enemy"))
    possible = set(_targets_by_spec(participants, actor, targeting))
    if targeting == "single_enemy":
        if not target_ids or target_ids[0] not in possible:
            return AbilityUseResult(False, "invalid_target", [])
        apply_to = [target_ids[0]]
    elif targeting == "self":
        apply_to = [actor.id]
    else:
        return AbilityUseResult(False, "unsupported_targeting", [])

    # spend resources
    ok, reason = can_use_ability(actor, ability_def)
    if not ok:
        return AbilityUseResult(False, reason, [])

    for k, v in (ability_def.get("resource_cost") or {}).items():
        _spend_resource(actor, k, float(v))

    # set cooldown
    cd = int(ability_def.get("cooldown", 0) or 0)
    if cd > 0:
        actor.cooldowns[ability_def.get("id", "")] = cd

    # body parts config
    body_cfg = load_body_parts(Path(__file__).parents[2] / "data" / "body_parts.yaml")

    # execute (attack-like)
    for tid in apply_to:
        tgt = next((c for c in participants if c.id == tid), None)
        if tgt is None or not tgt.is_alive():
            continue
        res = resolve_attack(actor, tgt, ability_def, body_cfg, rng)
        if res.hit:
            tgt.hp = max(0.0, tgt.hp - res.amount)
            evs.append(
                {
                    "type": "hit",
                    "target_id": tid,
                    "amount": res.amount,
                    "dtype": res.dtype,
                    "crit": res.crit,
                    "body_part": res.body_part,
                }
            )
            # on-hit effects
            for inst in apply_on_hit_effects(actor, tgt, ability_def, _load_status_cfg(), rng):
                evs.append({"type": "effect", "target_id": tid, "effect_id": inst.id})
        else:
            evs.append({"type": "miss", "target_id": tid})
    return AbilityUseResult(True, "", evs)


def _load_status_cfg():
    from ..loaders.status_effects_loader import load_status_effects
    from pathlib import Path

    return load_status_effects(Path(__file__).parents[2] / "data" / "status_effects.yaml")
