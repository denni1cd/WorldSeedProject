from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.engine.ai import choose_and_execute
from combat.loaders.abilities_loader import load_abilities
from combat.loaders.ai_rules_loader import load_ai_rules


def main():
    data_root = Path(__file__).parents[1] / "combat" / "data"
    abilities = load_abilities(data_root / "abilities.yaml")
    rules = load_ai_rules(data_root / "ai_rules.yaml")

    a = Combatant(
        "A",
        "Aria",
        {"ATT": 9, "DEX": 7, "ARM": 3, "WPN": 3},
        hp=30.0,
        mana=6.0,
        resist={},
        tags=["humanoid"],
        team="alpha",
    )
    b = Combatant(
        "B",
        "Belor",
        {"ATT": 6, "DEX": 8, "INT": 12, "ARM": 2, "WPN": 1},
        hp=28.0,
        mana=12.0,
        resist={"fire": 0.10},
        tags=["humanoid"],
        team="beta",
    )
    enc = Encounter([a, b], seed=888)

    for round_idx in range(1, 7):
        print(f"\n-- Round {round_idx} --")
        # actor is next turn
        actor = enc.next_turn()
        # AI chooses and executes
        outcome = choose_and_execute(enc.participants, actor, abilities, rules, enc.threat, enc.rng)
        if outcome["ok"]:
            # print summary
            tgt_names = [
                next((c.name for c in enc.participants if c.id == tid), tid)
                for tid in outcome["target_ids"]
            ]
            print(f"{actor.name} uses {outcome['ability_id']} on {', '.join(tgt_names)}")
            # update threat with resulting events
            enc.ingest_events_update_threat(outcome["events"])
        else:
            print(f"{actor.name} has no ready rule/ability.")

        # Stop if one side dead
        alphas = [c for c in enc.participants if c.team == "alpha" and c.is_alive()]
        betas = [c for c in enc.participants if c.team == "beta" and c.is_alive()]
        if not alphas or not betas:
            winner = "alpha" if alphas else "beta"
            print(f"\nWinner: {winner}")
            break

    print(f"\nThreat (per victim→attacker): {enc.threat}")


if __name__ == "__main__":
    main()
