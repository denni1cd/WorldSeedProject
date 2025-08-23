from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def _mk_duo():
    a = Combatant(
        id="A",
        name="Aria",
        stats={"ATT": 8, "DEX": 7, "ARM": 3, "WPN": 3},
        hp=30.0,
        mana=6.0,
        resist={},
        tags=["humanoid"],
        team="alpha",
    )
    b = Combatant(
        id="B",
        name="Belor",
        stats={"ATT": 6, "DEX": 8, "INT": 12, "ARM": 2, "WPN": 1},
        hp=28.0,
        mana=12.0,
        resist={"fire": 0.10},
        tags=["humanoid"],
        team="beta",
    )
    return a, b


def main():
    a, b = _mk_duo()
    enc = Encounter([a, b], seed=2025)

    # Play two turns, then snapshot
    for _ in range(2):
        enc.next_turn()  # advance pointer deterministically
    snap = enc.snapshot()

    # Restore into a fresh encounter with same participants
    c, d = _mk_duo()
    enc2 = Encounter([c, d], seed=999)  # seed doesn't matter after restore
    enc2.restore(snap)

    # Advance both encounters in lockstep for 5 more turns; compare events length
    for _ in range(5):
        actor1 = enc.next_turn()
        actor2 = enc2.next_turn()
        assert actor1.id == actor2.id  # same actor order
    print("Snapshot/restore sanity OK (actors match).")


if __name__ == "__main__":
    main()
