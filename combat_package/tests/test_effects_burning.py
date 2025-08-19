from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.effects import apply_status, tick_start_of_turn
from combat.loaders.status_effects_loader import load_status_effects
from pathlib import Path


def test_burning_ticks_and_expires(tmp_path):
    cfg = load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )
    victim = Combatant(
        "V", "Victim", {"INT": 10}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"]
    )
    # apply burning
    inst = apply_status(victim, "burning", cfg, source_id="S")
    assert inst and victim.statuses and victim.statuses[0]["id"] == "burning"
    # tick for duration turns
    from combat.engine.rng import RandomSource

    rng = RandomSource(1)
    for _ in range(3):
        evs = tick_start_of_turn(victim, cfg, rng)
        assert any(e["effect_id"] == "burning" for e in evs)
    # now burning should be gone
    evs = tick_start_of_turn(victim, cfg, rng)
    assert not any(e["effect_id"] == "burning" for e in evs)


def test_burning_respects_resistance():
    from combat.engine.rng import RandomSource

    cfg = load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )
    v1 = Combatant(
        "V1", "V1", {"INT": 10}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"]
    )
    v2 = Combatant(
        "V2",
        "V2",
        {"INT": 10},
        hp=20.0,
        mana=0.0,
        resist={"fire": 0.5},
        tags=["humanoid"],
    )
    apply_status(v1, "burning", cfg)
    apply_status(v2, "burning", cfg)
    rng = RandomSource(2)
    evs1 = tick_start_of_turn(v1, cfg, rng)
    dmg1 = sum(e["amount"] for e in evs1)
    evs2 = tick_start_of_turn(v2, cfg, rng)
    dmg2 = sum(e["amount"] for e in evs2)
    assert dmg2 < dmg1
