from __future__ import annotations
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter


def main():
    a = Combatant(
        id="A",
        name="Aria the Fighter",
        stats={"ATT": 8, "DEX": 7, "ARM": 3, "WPN": 3},
        hp=30.0,
        mana=10.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        id="B",
        name="Belor the Wizard",
        stats={"ATT": 6, "DEX": 8, "INT": 9, "ARM": 2, "WPN": 1},
        hp=26.0,
        mana=18.0,
        resist={"fire": 0.10},
        tags=["humanoid"],
    )

    enc = Encounter([a, b], seed=1337)
    for _ in range(5):
        r = enc.run_round()
        for line in enc.log[-2:]:
            print("•", line)
        if r.get("ended"):
            print(f"\nWinner: {r.get('winner')}")
            break


if __name__ == "__main__":
    main()
