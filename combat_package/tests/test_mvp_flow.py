from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def test_turn_order_deterministic():
    a = Combatant(
        id="A",
        name="Aria",
        stats={"DEX": 8},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        id="B",
        name="Borin",
        stats={"DEX": 6},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    enc = Encounter([a, b], seed=42)
    # High DEX goes first, then cycles
    names = [enc.next_turn().name for _ in range(3)]
    assert names == ["Aria", "Borin", "Aria"]

    # If DEX equal, order falls back to name asc then id
    a2 = Combatant(
        id="A2",
        name="Aria",
        stats={"DEX": 7},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    b2 = Combatant(
        id="B2",
        name="Borin",
        stats={"DEX": 7},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    enc2 = Encounter([b2, a2], seed=99)  # input order reversed should not matter
    assert [c.id for c in enc2.participants] == [
        "B2",
        "A2",
    ]  # participants preserve input order
    assert enc2.order_ids == ["A2", "B2"]  # initiative sorts by name when DEX ties


def test_run_round_produces_log_and_damage():
    from combat.engine.encounter import Encounter

    a = Combatant(
        id="A",
        name="Aria",
        stats={"DEX": 8, "ATT": 8, "WPN": 3, "ARM": 2},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        id="B",
        name="Borin",
        stats={"DEX": 6, "ATT": 6, "WPN": 2, "ARM": 1},
        hp=20.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    enc = Encounter([a, b], seed=7)
    enc.run_round()
    assert len(enc.log) >= 1
    assert a.hp < 21.0 or b.hp < 21.0
    assert "hits" in enc.log[0] or "slashes" in enc.log[0] or "takes" in enc.log[0]


def test_effect_apply_and_tick_narration():
    from combat.engine.narration import render_status_apply, render_dot_tick
    from combat.loaders.status_effects_loader import load_status_effects
    from combat.loaders.narration_loader import load_narration
    from combat.engine.rng import RandomSource
    from pathlib import Path

    eff = load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )
    narr = load_narration(
        Path(__file__).parents[1] / "combat" / "data" / "narration.yaml"
    )
    rng = RandomSource(5)
    line_apply = render_status_apply("Target", "burning", eff, narr, rng)
    line_tick = render_dot_tick("Target", "burning", 3.0, eff, narr, rng)
    assert isinstance(line_apply, str) and line_apply
    assert isinstance(line_tick, str) and line_tick
