from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def test_turn_order_deterministic():
    a = Combatant(
        id="A", name="Aria", stats={"DEX": 8}, hp=20.0, mana=10.0, resist={}, tags=["humanoid"]
    )
    b = Combatant(
        id="B", name="Borin", stats={"DEX": 6}, hp=20.0, mana=10.0, resist={}, tags=["humanoid"]
    )
    enc = Encounter([a, b], seed=42)
    # High DEX goes first, then cycles
    names = [enc.next_turn().name for _ in range(3)]
    assert names == ["Aria", "Borin", "Aria"]

    # If DEX equal, order falls back to name asc then id
    a2 = Combatant(
        id="A2", name="Aria", stats={"DEX": 7}, hp=20.0, mana=10.0, resist={}, tags=["humanoid"]
    )
    b2 = Combatant(
        id="B2", name="Borin", stats={"DEX": 7}, hp=20.0, mana=10.0, resist={}, tags=["humanoid"]
    )
    enc2 = Encounter([b2, a2], seed=99)  # input order reversed should not matter
    assert [c.id for c in enc2.participants] == ["B2", "A2"]  # participants preserve input order
    assert enc2.order_ids == ["A2", "B2"]  # initiative sorts by name when DEX ties
