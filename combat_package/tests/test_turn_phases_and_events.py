from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def test_event_log_types_exist_and_cycle_rounds():
    a = Combatant(
        "A",
        "A",
        {"DEX": 8, "ATT": 8, "WPN": 3, "ARM": 2},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t1",
    )
    b = Combatant(
        "B",
        "B",
        {"DEX": 6, "ATT": 6, "WPN": 2, "ARM": 1},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t2",
    )
    enc = Encounter([a, b], seed=7)
    # run a few turns; ensure events get populated by run_until (basic attack auto)
    result = enc.run_until(max_rounds=3)
    assert isinstance(result, dict)
    assert isinstance(enc.events, list)
    assert any(e["type"] in ("hit", "miss") for e in enc.events)
