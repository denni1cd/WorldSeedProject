from __future__ import annotations
from pathlib import Path
from ..combat.engine.combatant import Combatant
from ..combat.engine.encounter import Encounter
from ..combat.engine.ai import choose_and_execute
from ..combat.engine.narration import (
    render_dot_tick,
    render_hazard_event,
)
from ..combat.loaders.abilities_loader import load_abilities
from ..combat.loaders.ai_rules_loader import load_ai_rules
from ..combat.loaders.narration_loader import load_narration
from ..combat.loaders.status_effects_loader import load_status_effects
from ..combat.loaders.hazards_loader import load_hazards


def main():
    data_root = Path(__file__).parents[1] / "combat" / "data"
    abilities = load_abilities(data_root / "abilities.yaml")
    rules = load_ai_rules(data_root / "data" / "ai_rules.yaml")
    narr = load_narration(data_root / "narration.yaml")
    effs = load_status_effects(data_root / "status_effects.yaml")
    hazards_cfg = load_hazards(data_root / "hazards.yaml")

    a = Combatant(
        "A",
        "Aria",
        {"ATT": 9, "DEX": 7, "ARM": 3, "WPN": 3},
        hp=26.0,
        mana=6.0,
        resist={},
        tags=["humanoid"],
        team="alpha",
        location="lava",
    )
    b = Combatant(
        "B",
        "Belor",
        {"ATT": 6, "DEX": 8, "INT": 12, "ARM": 2, "WPN": 1},
        hp=28.0,
        mana=12.0,
        resist={"fire": 0.10},
        tags=["humanoid", "flying"],
        team="beta",
        location="fountain",
    )
    enc = Encounter([a, b], seed=909)

    for round_idx in range(1, 5):
        print(f"\n== Round {round_idx} ==")

        # start_of_turn hazards + DoT tick + AI action for each actor
        for _ in range(len(enc.participants)):
            actor = enc.next_turn()

            # Hazards at start_of_turn
            for ev in enc.process_hazards("start_of_turn"):
                # Show only hazard lines
                print("•", render_hazard_event(ev, hazards_cfg, enc.rng))

            # Status DoTs
            from ..combat.engine.effects import tick_start_of_turn

            for ev in tick_start_of_turn(actor, effs, enc.rng):
                print(
                    "•",
                    render_dot_tick(actor.name, ev["effect_id"], ev["amount"], effs, narr, enc.rng),
                )

            # AI action (using your rules)
            outcome = choose_and_execute(
                enc.participants, actor, abilities, rules, enc.threat, enc.rng
            )
            if outcome["ok"]:
                enc.ingest_events_update_threat(outcome["events"])

            # Hazards at end_of_turn
            for ev in enc.process_hazards("end_of_turn"):
                print("•", render_hazard_event(ev, hazards_cfg, enc.rng))

        # (Optional) you could decrement finite hazard durations here if you add such hazards later.

    print(
        f"\nFinal → {a.name}: HP {a.hp:.1f}, Mana {a.mana:.1f} | {b.name}: HP {b.hp:.1f}, Mana {b.mana:.1f}"
    )


if __name__ == "__main__":
    main()
