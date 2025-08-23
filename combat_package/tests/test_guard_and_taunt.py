from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.effects import apply_status
from combat.engine.abilities import execute_ability
from combat.engine.rng import RandomSource
from pathlib import Path
from combat.loaders.status_effects_loader import load_status_effects


def _status_cfg():
    return load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )


def test_guard_reduces_next_hit_and_consumes():
    cfg = _status_cfg()
    a = Combatant(
        "A",
        "A",
        {"ATT": 10, "DEX": 8, "WPN": 4},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t1",
    )
    b = Combatant(
        "B",
        "B",
        {"ATT": 10, "DEX": 5, "WPN": 4},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t2",
    )
    # apply guarding to A
    apply_status(a, "guarding", cfg, source_id="A")
    print(f"Applied guarding, statuses: {a.statuses}")
    # synthetic heavy hit ability
    ability = {
        "id": "smash",
        "name": "Smash",
        "kind": "attack",
        "formula": "ATT + WPN + 6",
        "damage_type": "slashing",
        "targeting": "single_enemy",
        "crit": {"chance": "0.0", "multiplier": 1.5},
        "resource_cost": {},
        "cooldown": 0,
    }
    res1 = execute_ability([a, b], b, ability, [a.id], RandomSource(1))
    print(f"First hit events: {res1.events}")
    print(f"First hit HP: {a.hp}")
    # ensure guard_block event present and damage reduced
    amounts = [ev["amount"] for ev in (res1.events or []) if ev["type"] == "hit"]
    blocks = [ev["reduced"] for ev in (res1.events or []) if ev["type"] == "guard_block"]

    assert amounts and blocks and blocks[0] > 0.0
    # second hit should NOT block again (guard was consumed)
    res2 = execute_ability([a, b], b, ability, [a.id], RandomSource(2))
    print(f"Second hit events: {res2.events}")
    print(f"Second hit HP: {a.hp}")
    blocks2 = [ev for ev in (res2.events or []) if ev["type"] == "guard_block"]
    assert not blocks2
    # Check that guard status was consumed (removed from statuses)
    assert not any(s["id"] == "guarding" for s in a.statuses)


def test_taunt_restricts_target_choice():
    cfg = _status_cfg()
    t1 = Combatant(
        "T1",
        "Taunter",
        {"DEX": 7},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="A",
    )
    x = Combatant(
        "X",
        "Victim",
        {"ATT": 8, "DEX": 6},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="B",
    )
    y = Combatant(
        "Y",
        "Bystander",
        {"DEX": 6},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="B",
    )
    apply_status(x, "taunted", cfg, source_id="T1")
    # ability auto target (no target_ids) should hit T1 (taunt source)
    ability = {
        "id": "poke",
        "name": "Poke",
        "kind": "attack",
        "formula": "ATT",
        "damage_type": "slashing",
        "targeting": "single_enemy",
        "crit": {"chance": "0.0", "multiplier": 1.5},
        "resource_cost": {},
        "cooldown": 0,
    }
    res = execute_ability([t1, x, y], x, ability, [], RandomSource(3))
    targets = [ev["target_id"] for ev in (res.events or []) if ev["type"] in ("hit", "miss")]
    assert targets and targets[0] == "T1"
