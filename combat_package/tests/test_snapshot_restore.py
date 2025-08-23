from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def test_snapshot_restore_determinism_actor_order():
    a = Combatant("A", "A", {"DEX": 8}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t1")
    b = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t2")
    enc = Encounter([a, b], seed=123)
    # step once then snapshot
    enc.next_turn()
    snap = enc.snapshot()
    # restore into new encounter
    a2 = Combatant("A", "A", {"DEX": 8}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t1")
    b2 = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t2")
    enc2 = Encounter([a2, b2], seed=999)
    enc2.restore(snap)
    # next actors must match
    assert enc.next_turn().id == enc2.next_turn().id
