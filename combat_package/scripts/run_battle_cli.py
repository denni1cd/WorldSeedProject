from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.engine.resolution import resolve_attack
from combat.engine.effects import apply_on_hit_effects, tick_start_of_turn
from combat.engine.narration import render_event, render_status_apply, render_dot_tick
from combat.loaders.abilities_loader import load_abilities
from combat.loaders.status_effects_loader import load_status_effects
from combat.loaders.narration_loader import load_narration


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
        stats={"ATT": 6, "DEX": 8, "INT": 12, "ARM": 2, "WPN": 1},
        hp=26.0,
        mana=18.0,
        resist={"fire": 0.10},
        tags=["humanoid"],
    )

    enc = Encounter([a, b], seed=1337)
    data_root = Path(__file__).parents[1] / "combat" / "data"
    abilities = load_abilities(data_root / "abilities.yaml")
    status_cfg = load_status_effects(data_root / "status_effects.yaml")
    narr = load_narration(data_root / "narration.yaml")

    # Add a simple fireball ability on the fly if not present
    fireball = next(
        (x for x in abilities.get("abilities", []) if x.get("id") == "fireball"), None
    )
    if not fireball:
        fireball = {
            "id": "fireball",
            "name": "Fireball",
            "formula": "INT*1.2 + 6",
            "damage_type": "fire",
            "crit": {"chance": "0.10 + DEX*0.002", "multiplier": 1.5},
            "on_hit": {"apply_status": [{"id": "burning", "chance": 1.0}]},
        }
        abilities.setdefault("abilities", []).append(fireball)
    basic = next(
        (x for x in abilities.get("abilities", []) if x.get("id") == "basic_attack"),
        None,
    )
    if not basic:
        basic = {
            "id": "basic_attack",
            "name": "Basic Attack",
            "formula": "ATT + WPN - ARM*0.6",
            "damage_type": "slashing",
            "crit": {"chance": "0.05 + DEX*0.002", "multiplier": 1.5},
        }
        abilities["abilities"].append(basic)

    for round_idx in range(1, 6):
        print(f"\n-- Round {round_idx} --")
        # start-of-turn ticks (A then B)
        for actor in [a, b]:
            evs = tick_start_of_turn(actor, status_cfg, enc.rng)
            for ev in evs:
                print(
                    "•",
                    render_dot_tick(
                        actor.name,
                        ev["effect_id"],
                        ev["amount"],
                        status_cfg,
                        narr,
                        enc.rng,
                    ),
                )

        # A uses basic attack on B
        r1 = resolve_attack(
            a,
            b,
            basic,
            {"groups": {"humanoid": ["chest", "arm", "leg"]}, "weights": {}},
            enc.rng,
        )
        print(
            "•",
            render_event(
                {
                    "actor": a.name,
                    "target": b.name,
                    "hit": r1.hit,
                    "crit": r1.crit,
                    "amount": r1.amount,
                    "dtype": r1.dtype,
                    "body_part": r1.body_part,
                },
                narr,
                enc.rng,
            ),
        )
        if r1.hit:
            b.hp = max(0.0, b.hp - r1.amount)

        # B uses fireball on A (apply burning)
        r2 = resolve_attack(
            b,
            a,
            fireball,
            {"groups": {"humanoid": ["chest", "arm", "leg"]}, "weights": {}},
            enc.rng,
        )
        print(
            "•",
            render_event(
                {
                    "actor": b.name,
                    "target": a.name,
                    "hit": r2.hit,
                    "crit": r2.crit,
                    "amount": r2.amount,
                    "dtype": r2.dtype,
                    "body_part": r2.body_part,
                },
                narr,
                enc.rng,
            ),
        )
        if r2.hit:
            a.hp = max(0.0, a.hp - r2.amount)
            insts = apply_on_hit_effects(b, a, fireball, status_cfg, enc.rng)
            for inst in insts:
                print(
                    "•", render_status_apply(a.name, inst.id, status_cfg, narr, enc.rng)
                )

        if a.hp <= 0 or b.hp <= 0:
            break

    print(f"\nFinal HP → {a.name}: {a.hp} | {b.name}: {b.hp}")


if __name__ == "__main__":
    main()
