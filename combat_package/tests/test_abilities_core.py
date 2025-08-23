from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.abilities import can_use_ability, execute_ability
from combat.engine.rng import RandomSource
from combat.loaders.abilities_loader import load_abilities


def _load_abilities():
    return load_abilities(Path(__file__).parents[1] / "combat" / "data" / "abilities.yaml")


def _ability(abilities, aid: str):
    return next((x for x in abilities.get("abilities", []) if x.get("id") == aid), None)


def test_resource_cost_and_cooldown_applied():
    abilities = _load_abilities()
    fireball = _ability(abilities, "fireball")
    a = Combatant(
        "A",
        "Caster",
        {"INT": 12, "DEX": 8},
        hp=20.0,
        mana=6.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        "B",
        "Target",
        {"DEX": 1, "ARM": 0},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    ok, reason = can_use_ability(a, fireball)
    assert ok
    res = execute_ability([a, b], a, fireball, [b.id], RandomSource(9))
    assert res.ok
    # mana spent and cooldown set
    assert a.mana < 6.0
    assert a.cooldowns.get("fireball", 0) >= 1


def test_insufficient_mana_prevents_cast():
    abilities = _load_abilities()
    fireball = _ability(abilities, "fireball")
    a = Combatant(
        "A",
        "Caster",
        {"INT": 12, "DEX": 8},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    ok, reason = can_use_ability(a, fireball)
    assert not ok and "insufficient_mana" in reason


def test_invalid_target_rejected():
    abilities = _load_abilities()
    fireball = _ability(abilities, "fireball")
    a = Combatant(
        "A",
        "Caster",
        {"INT": 12, "DEX": 8},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        "B",
        "Target",
        {"DEX": 1, "ARM": 0},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    res = execute_ability([a, b], a, fireball, ["Z"], RandomSource(1))
    assert not res.ok and res.reason == "invalid_target"


def test_cooldown_ticks_down():
    abilities = _load_abilities()
    fireball = _ability(abilities, "fireball")
    a = Combatant(
        "A",
        "Caster",
        {"INT": 12, "DEX": 8},
        hp=20.0,
        mana=20.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        "B",
        "Target",
        {"DEX": 1, "ARM": 0},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
    )
    # first cast ok
    res1 = execute_ability([a, b], a, fireball, [b.id], RandomSource(2))
    assert res1.ok
    # immediate second cast blocked due to cooldown
    ok2, reason2 = can_use_ability(a, fireball)
    assert not ok2 and reason2 == "on_cooldown"
    # tick cooldown twice → ready
    from combat.engine.encounter import Encounter

    enc = Encounter([a, b], seed=3)
    enc.tick_cooldowns(a)
    enc.tick_cooldowns(a)
    ok3, _ = can_use_ability(a, fireball)
    assert ok3
