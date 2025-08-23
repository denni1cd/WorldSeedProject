from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.engine.abilities import execute_ability, can_use_ability
from combat.engine.effects import tick_start_of_turn
from combat.engine.narration import render_event, render_status_apply, render_dot_tick
from combat.loaders.abilities_loader import load_abilities
from combat.loaders.narration_loader import load_narration
from combat.loaders.status_effects_loader import load_status_effects


def main():
    a = Combatant(
        id="A",
        name="Aria the Fighter",
        stats={"ATT": 8, "DEX": 7, "ARM": 3, "WPN": 3},
        hp=32.0,
        mana=6.0,
        resist={},
        tags=["humanoid"],
    )
    b = Combatant(
        id="B",
        name="Belor the Wizard",
        stats={"ATT": 6, "DEX": 8, "INT": 12, "ARM": 2, "WPN": 1},
        hp=28.0,
        mana=12.0,
        resist={"fire": 0.10},
        tags=["humanoid"],
    )

    enc = Encounter([a, b], seed=777)
    data_root = Path(__file__).parents[1] / "combat" / "data"
    abilities = load_abilities(data_root / "abilities.yaml")
    narr = load_narration(data_root / "narration.yaml")
    status_cfg = load_status_effects(data_root / "status_effects.yaml")

    # helpers
    def ability_by_id(aid: str):
        return next((x for x in abilities.get("abilities", []) if x.get("id") == aid), None)

    basic = ability_by_id("basic_attack")
    fireball = ability_by_id("fireball")

    for round_idx in range(1, 6):
        print(f"\n-- Round {round_idx} --")

        # Start-of-turn: A ticks cooldowns + statuses
        enc.tick_cooldowns(a)
        for ev in tick_start_of_turn(a, status_cfg, enc.rng):
            print(
                "•",
                render_dot_tick(a.name, ev["effect_id"], ev["amount"], status_cfg, narr, enc.rng),
            )
        # A tries to use fireball if enough mana, else basic
        use_fire = can_use_ability(a, fireball)[0] if fireball else False
        ab = fireball if use_fire else basic
        res = execute_ability(enc.participants, a, ab, [b.id], enc.rng)
        for ev in res.events or []:
            if ev["type"] == "hit" or ev["type"] == "miss":
                print(
                    "•",
                    render_event(
                        {
                            "actor": a.name,
                            "target": b.name,
                            "hit": ev["type"] == "hit",
                            "crit": ev.get("crit", False),
                            "amount": ev.get("amount", 0.0),
                            "dtype": ev.get("dtype", "slashing"),
                            "body_part": ev.get("body_part", "chest"),
                        },
                        narr,
                        enc.rng,
                    ),
                )
            elif ev["type"] == "effect":
                print(
                    "•",
                    render_status_apply(b.name, ev["effect_id"], status_cfg, narr, enc.rng),
                )

        if not b.is_alive():
            break

        # Start-of-turn: B ticks cooldowns + statuses
        enc.tick_cooldowns(b)
        for ev in tick_start_of_turn(b, status_cfg, enc.rng):
            print(
                "•",
                render_dot_tick(b.name, ev["effect_id"], ev["amount"], status_cfg, narr, enc.rng),
            )
        # B always uses fireball if possible else basic
        use_fire_b = can_use_ability(b, fireball)[0] if fireball else False
        ab_b = fireball if use_fire_b else basic
        res_b = execute_ability(enc.participants, b, ab_b, [a.id], enc.rng)
        for ev in res_b.events or []:
            if ev["type"] == "hit" or ev["type"] == "miss":
                print(
                    "•",
                    render_event(
                        {
                            "actor": b.name,
                            "target": a.name,
                            "hit": ev["type"] == "hit",
                            "crit": ev.get("crit", False),
                            "amount": ev.get("amount", 0.0),
                            "dtype": ev.get("dtype", "slashing"),
                            "body_part": ev.get("body_part", "chest"),
                        },
                        narr,
                        enc.rng,
                    ),
                )
            elif ev["type"] == "effect":
                print(
                    "•",
                    render_status_apply(a.name, ev["effect_id"], status_cfg, narr, enc.rng),
                )

        if not a.is_alive():
            break

    print(
        f"\nFinal → {a.name}: HP {a.hp:.1f}, Mana {a.mana:.1f} | {b.name}: HP {b.hp:.1f}, Mana {b.mana:.1f}"
    )


if __name__ == "__main__":
    main()
