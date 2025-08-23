from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.resolution import resolve_attack
from combat.engine.rng import RandomSource

ABILITY = {
    "id": "basic_attack",
    "formula": "ATT + WPN - ARM*0.6",
    "damage_type": "slashing",
    "crit": {"chance": "0.0", "multiplier": 1.5},
}
BODY = {"groups": {"humanoid": ["chest"]}, "weights": {"humanoid": {"chest": 1.0}}}


def test_crit_increases_damage():
    atk = Combatant(
        "A",
        "A",
        {"ATT": 10, "DEX": 10, "WPN": 5},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    tgt = Combatant("B", "B", {"DEX": 1, "ARM": 0}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"])
    # non-crit
    r1 = resolve_attack(atk, tgt, ABILITY, BODY, RandomSource(seed=1))
    assert r1.hit
    base_amt = r1.amount
    # force crit by setting chance=1.0
    ability_crit = dict(ABILITY)
    ability_crit["crit"] = {"chance": "1.0", "multiplier": 1.5}
    # Try multiple seeds to find one that hits
    for seed in range(10, 20):
        r2 = resolve_attack(atk, tgt, ability_crit, BODY, RandomSource(seed=seed))
        if r2.hit:
            assert r2.crit
            assert r2.amount > base_amt
            return
    # If we get here, all seeds missed - that's unlikely but possible
    assert False, "Could not find a seed that produces a hit for crit test"


def test_resistance_reduces_damage():
    atk = Combatant(
        "A",
        "A",
        {"ATT": 10, "DEX": 10, "WPN": 5},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    tgt = Combatant(
        "B",
        "B",
        {"DEX": 1, "ARM": 0},
        hp=20.0,
        mana=0.0,
        resist={"slashing": 0.5},
        tags=["humanoid"],
    )
    r = resolve_attack(atk, tgt, ABILITY, BODY, RandomSource(seed=3))
    assert r.hit
    assert 0 < r.amount < 100
    # with 50% resist, amount should be about half of base 15 → ~7.5
    assert r.amount <= 8.0
