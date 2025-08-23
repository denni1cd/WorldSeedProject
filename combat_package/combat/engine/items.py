from __future__ import annotations
from typing import Dict, Any, List
from .combatant import Combatant
from .rng import RandomSource
from .effects import apply_status
from .resolution import resolve_attack
from ..loaders.body_parts_loader import load_body_parts
from pathlib import Path


def can_use_item(user: Combatant, item_def: Dict[str, Any]) -> tuple[bool, str]:
    count = int(user.inventory.get(item_def.get("id", ""), 0))
    if count <= 0:
        return False, "no_item"
    return True, ""


def use_item(
    participants: List[Combatant],
    user: Combatant,
    item_def: Dict[str, Any],
    target_ids: List[str],
    rng: RandomSource,
) -> Dict[str, Any]:
    """
    Executes an item:
      kind: "consumable" → effects {heal_hp:int, restore_mana:int, apply_status:[ids], cleanse_status:[ids]}
      kind: "throwable"  → fields {targeting, formula, damage_type}
    Decrements user.inventory for the item id on success.
    Returns dict { ok:bool, reason:str, events:list }
    """
    iid = item_def.get("id")
    evs: List[Dict[str, Any]] = []

    ok, reason = can_use_item(user, item_def)
    if not ok:
        return {"ok": False, "reason": reason, "events": []}

    kind = str(item_def.get("kind", "consumable"))
    if kind == "consumable":
        effects = item_def.get("effects") or {}
        # targets default to self for consumables
        if not target_ids:
            target_ids = [user.id]
        for tid in target_ids:
            tgt = next((c for c in participants if c.id == tid and c.is_alive()), None)
            if not tgt:
                continue
            if "heal_hp" in effects:
                amt = float(effects["heal_hp"])
                before = tgt.hp
                tgt.hp = before + amt
                evs.append({"type": "heal", "target_id": tid, "amount": amt})
            if "restore_mana" in effects:
                amt = float(effects["restore_mana"])
                tgt.mana = tgt.mana + amt
                evs.append({"type": "mana", "target_id": tid, "amount": amt})
            for sid in effects.get("apply_status", []) or []:
                inst = apply_status(tgt, sid, _load_status_cfg(), source_id=user.id)
                if inst:
                    evs.append({"type": "effect", "target_id": tid, "effect_id": sid})
            for sid in effects.get("cleanse_status", []) or []:
                _cleanse_status(tgt, sid)
                evs.append({"type": "cleanse", "target_id": tid, "effect_id": sid})
        # consume
        user.inventory[iid] = max(0, int(user.inventory.get(iid, 0)) - 1)
        return {"ok": True, "reason": "", "events": evs}

    if kind == "throwable":
        body_cfg = load_body_parts(Path(__file__).parents[2] / "data" / "body_parts.yaml")
        # default auto-pick one enemy if none supplied
        if not target_ids:
            enemies = [c for c in participants if c.is_alive() and c.team != user.team]
            if not enemies:
                return {"ok": False, "reason": "no_valid_target", "events": []}
            target_ids = [enemies[0].id]
        # synthesize an ability-like dict to reuse resolve_attack
        ability_like = {
            "id": f"item:{iid}",
            "formula": item_def.get("formula", "INT*0.4 + 6"),
            "damage_type": item_def.get("damage_type", "slashing"),
            "crit": {"chance": "0.0", "multiplier": 1.5},
        }
        for tid in target_ids:
            tgt = next((c for c in participants if c.id == tid and c.is_alive()), None)
            if not tgt:
                continue
            res = resolve_attack(user, tgt, ability_like, body_cfg, rng)
            if res.hit:
                # items ignore guard? keep consistent with abilities → call modify_incoming_damage
                from .effects import modify_incoming_damage

                new_amt, pre = modify_incoming_damage(tgt, res.amount, res.dtype)
                evs.extend(pre)
                tgt.hp = max(0.0, tgt.hp - new_amt)
                evs.append(
                    {
                        "type": "hit",
                        "actor_id": user.id,
                        "target_id": tid,
                        "amount": new_amt,
                        "dtype": res.dtype,
                        "item_id": iid,
                    }
                )
            else:
                evs.append(
                    {
                        "type": "miss",
                        "actor_id": user.id,
                        "target_id": tid,
                        "item_id": iid,
                    }
                )
        user.inventory[iid] = max(0, int(user.inventory.get(iid, 0)) - 1)
        return {"ok": True, "reason": "", "events": evs}

    return {"ok": False, "reason": "unsupported_item_kind", "events": []}


def _load_status_cfg():
    from ..loaders.status_effects_loader import load_status_effects
    from pathlib import Path

    return load_status_effects(Path(__file__).parents[2] / "data" / "status_effects.yaml")


def _cleanse_status(tgt: Combatant, eff_id: str) -> None:
    if not tgt.statuses:
        return
    tgt.statuses = [s for s in tgt.statuses if s.get("id") != eff_id]
