from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.abilities import execute_ability
from combat.engine.rng import RandomSource


def test_all_enemies_and_random_enemy_targeting():
    # three enemies on team "t2"
    a = Combatant(
        "A",
        "Caster",
        {"INT": 12, "DEX": 8},
        hp=20.0,
        mana=50.0,
        resist={},
        tags=["humanoid"],
        team="t1",
    )
    e1 = Combatant(
        "E1", "E1", {"DEX": 5}, hp=10.0, mana=0.0, resist={}, tags=["humanoid"], team="t2"
    )
    e2 = Combatant(
        "E2", "E2", {"DEX": 5}, hp=10.0, mana=0.0, resist={}, tags=["humanoid"], team="t2"
    )
    e3 = Combatant(
        "E3", "E3", {"DEX": 5}, hp=10.0, mana=0.0, resist={}, tags=["humanoid"], team="t2"
    )
    parts = [a, e1, e2, e3]
    # define synthetic AoE ability inline
    ability = {
        "id": "arc_sweep",
        "name": "Arc Sweep",
        "kind": "attack",
        "formula": "ATT + 2",
        "damage_type": "slashing",
        "targeting": "all_enemies",
        "crit": {"chance": "0.0", "multiplier": 1.5},
        "resource_cost": {},
        "cooldown": 0,
    }
    res = execute_ability(parts, a, ability, [], RandomSource(1))
    assert res.ok and len([ev for ev in (res.events or []) if ev["type"] in ("hit", "miss")]) >= 3

    # random_enemy should pick one of the three
    ability2 = {
        "id": "stab",
        "name": "Stab",
        "kind": "attack",
        "formula": "ATT + 1",
        "damage_type": "slashing",
        "targeting": "random_enemy",
        "crit": {"chance": "0.0", "multiplier": 1.5},
        "resource_cost": {},
        "cooldown": 0,
    }
    res2 = execute_ability(parts, a, ability2, [], RandomSource(2))
    assert res2.ok and len([ev for ev in (res2.events or []) if ev["type"] in ("hit", "miss")]) == 1
