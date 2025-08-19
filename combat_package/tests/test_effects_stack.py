from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.effects import apply_status, tick_start_of_turn
from combat.loaders.status_effects_loader import load_status_effects
from pathlib import Path
from combat.engine.rng import RandomSource


def test_poison_stacks_up_to_cap_and_persists():
    cfg = load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )
    v = Combatant(
        "V", "Victim", {"INT": 20}, hp=30.0, mana=0.0, resist={}, tags=["humanoid"]
    )
    # apply poison thrice, duration should not reset (stack_mode=add)
    apply_status(v, "poison", cfg)
    apply_status(v, "poison", cfg)
    apply_status(v, "poison", cfg)
    assert v.statuses[0]["stacks"] == 3
    rng = RandomSource(3)
    total_ticks = 0
    for _ in range(4):
        evs = tick_start_of_turn(v, cfg, rng)
        total_ticks += len(evs)
    # Poison expired after 4 ticks
    evs = tick_start_of_turn(v, cfg, rng)
    assert not evs
    assert v.hp < 30.0
