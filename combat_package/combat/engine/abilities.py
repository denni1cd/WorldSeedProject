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


def _is_enemy(a: Combatant, b: Combatant) -> bool:
    return a.team != b.team


def _targets_by_spec(
    participants: List[Combatant], actor: Combatant, spec: str, rng: RandomSource
) -> List[str]:
    living = [c for c in participants if c.is_alive()]
    enemies = [c for c in living if _is_enemy(actor, c)]
    allies = [c for c in living if (c.team == actor.team)]

    if spec == "self":
        return [actor.id]
    if spec == "single_enemy":
        return [enemies[0].id] if enemies else []
    if spec == "random_enemy":
        return [rng.choice(enemies).id] if enemies else []
    if spec == "all_enemies":
        return [c.id for c in enemies]
    if spec == "ally_lowest_hp":
        if not allies:
            return []
        tgt = min(allies, key=lambda c: c.hp)
        return [tgt.id]
    return []


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
      - hit/miss entries: {"type":"hit","actor_id":...,"target_id":...,"ability_id":...,"amount":...,"dtype":...,"crit":bool,"body_part":...}
      - effect entries:   {"type":"effect","actor_id":...,"target_id":...,"effect_id":...}
    """
    evs: List[Dict[str, Any]] = []
    targeting = str(ability_def.get("targeting", "single_enemy"))
    possible = set(_targets_by_spec(participants, actor, targeting, rng))

    # normalize target_ids based on targeting
    if targeting in ("single_enemy", "random_enemy", "ally_lowest_hp", "self"):
        if not possible:
            return AbilityUseResult(False, "no_valid_target", [])
        # if caller didn't supply, auto-pick first possible for convenience
        if not target_ids:
            target_ids = [next(iter(possible))]
        if target_ids[0] not in possible:
            return AbilityUseResult(False, "invalid_target", [])
        apply_to = [target_ids[0]]
    elif targeting == "all_enemies":
        apply_to = list(possible)
        if not apply_to:
            return AbilityUseResult(False, "no_valid_target", [])
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
        tgt = next((c for c in participants if c.id == tid and c.is_alive()), None)
        if not tgt:
            continue
        res = resolve_attack(actor, tgt, ability_def, body_cfg, rng)
        if res.hit:
            tgt.hp = max(0.0, tgt.hp - res.amount)
            evs.append(
                {
                    "type": "hit",
                    "actor_id": actor.id,
                    "target_id": tid,
                    "ability_id": ability_def.get("id"),
                    "amount": res.amount,
                    "dtype": res.dtype,
                    "crit": res.crit,
                    "body_part": res.body_part,
                }
            )
            # on-hit effects
            for inst in apply_on_hit_effects(actor, tgt, ability_def, _load_status_cfg(), rng):
                evs.append(
                    {
                        "type": "effect",
                        "actor_id": actor.id,
                        "target_id": tid,
                        "ability_id": ability_def.get("id"),
                        "effect_id": inst.id,
                    }
                )
        else:
            evs.append(
                {
                    "type": "miss",
                    "actor_id": actor.id,
                    "target_id": tid,
                    "ability_id": ability_def.get("id"),
                }
            )
    return AbilityUseResult(True, "", evs)


def _load_status_cfg():
    from ..loaders.status_effects_loader import load_status_effects
    from pathlib import Path

    return load_status_effects(Path(__file__).parents[2] / "data" / "status_effects.yaml")
