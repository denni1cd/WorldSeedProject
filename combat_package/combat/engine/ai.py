from __future__ import annotations
from typing import Dict, Any, List
from .combatant import Combatant
from .rng import RandomSource
from .abilities import can_use_ability, execute_ability
from .threat import highest_threat_target


# Minimal target selectors used by rules
def _enemy_ids(participants: List[Combatant], actor: Combatant) -> List[str]:
    return [c.id for c in participants if c.is_alive() and c.team != actor.team]


def _ally_ids(participants: List[Combatant], actor: Combatant) -> List[str]:
    return [c.id for c in participants if c.is_alive() and c.team == actor.team]


def _lowest_hp_enemy(participants: List[Combatant], actor: Combatant) -> str | None:
    enemies = [c for c in participants if c.is_alive() and c.team != actor.team]
    if not enemies:
        return None
    return min(enemies, key=lambda c: c.hp).id


def _random_enemy(participants: List[Combatant], actor: Combatant, rng: RandomSource) -> str | None:
    enemies = [c for c in participants if c.is_alive() and c.team != actor.team]
    return rng.choice(enemies).id if enemies else None


def _all_enemies(participants: List[Combatant], actor: Combatant) -> List[str]:
    return _enemy_ids(participants, actor)


def _target_from_rule(
    rule_target: str,
    participants: List[Combatant],
    actor: Combatant,
    rng: RandomSource,
    threat_table,
) -> List[str]:
    if rule_target == "self":
        return [actor.id]
    if rule_target == "highest_threat":
        cands = _enemy_ids(participants, actor)
        if not cands:
            return []
        pick = highest_threat_target(threat_table, actor.id, cands) or cands[0]
        return [pick]
    if rule_target == "lowest_hp_enemy":
        tid = _lowest_hp_enemy(participants, actor)
        return [tid] if tid else []
    if rule_target == "random_enemy":
        tid = _random_enemy(participants, actor, rng)
        return [tid] if tid else []
    if rule_target == "all_enemies":
        return _all_enemies(participants, actor)
    # default fallback: highest_threat
    cands = _enemy_ids(participants, actor)
    return [cands[0]] if cands else []


def _require_ok(
    require: Dict[str, Any], actor: Combatant, target: Combatant | None, ability_def: Dict[str, Any]
) -> bool:
    # absolute thresholds (avoid needing max_hp)
    hp_le = require.get("self_hp_le")
    if hp_le is not None and not (actor.hp <= float(hp_le)):
        return False
    mana_ge = require.get("self_mana_ge")
    if mana_ge is not None and not (actor.mana + 1e-9 >= float(mana_ge)):
        return False
    # optional target hp threshold
    t_hp_le = require.get("target_hp_le")
    if t_hp_le is not None and (not target or not (target.hp <= float(t_hp_le))):
        return False
    # ready check
    if require.get("ability_ready", False):
        ok, _ = can_use_ability(actor, ability_def)
        if not ok:
            return False
    # status checks (simple)
    present = set(s.get("id") for s in (actor.statuses or []))
    needs_absent = require.get("self_status_absent") or []
    for sid in needs_absent:
        if sid in present:
            return False
    needs_present = require.get("self_status_present") or []
    for sid in needs_present:
        if sid not in present:
            return False
    return True


def choose_and_execute(
    participants: List[Combatant],
    actor: Combatant,
    abilities_bundle: Dict[str, Any],
    ai_rules: Dict[str, Any],
    threat_table,
    rng: RandomSource,
) -> Dict[str, Any]:
    """
    Returns: {"ok": bool, "reason": str, "ability_id": str|None, "target_ids": list[str], "events": list[dict]}
    """
    rules = (ai_rules.get("ai") or {}).get("rules", [])

    # helper to fetch ability def by id
    def ab(aid: str) -> Dict[str, Any] | None:
        for x in abilities_bundle.get("abilities") or []:
            if x.get("id") == aid:
                return x
        return None

    for rule in rules:
        aid = str(rule.get("ability", ""))
        ability_def = ab(aid)
        if not ability_def:
            continue
        # compute target_ids according to rule target selector
        t_ids = _target_from_rule(
            str(rule.get("target", "highest_threat")), participants, actor, rng, threat_table
        )
        first_target = next((c for c in participants if t_ids and c.id == t_ids[0]), None)
        if not _require_ok(rule.get("require", {}), actor, first_target, ability_def):
            continue
        # try execution (validates resources/cooldowns internally)

        res = execute_ability(participants, actor, ability_def, t_ids, rng)
        if res.ok:
            return {
                "ok": True,
                "reason": "",
                "ability_id": aid,
                "target_ids": t_ids,
                "events": res.events or [],
            }
    return {
        "ok": False,
        "reason": "no_rule_matched_or_not_ready",
        "ability_id": None,
        "target_ids": [],
        "events": [],
    }
