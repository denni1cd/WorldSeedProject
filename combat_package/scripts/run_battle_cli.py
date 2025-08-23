from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.engine.abilities import execute_ability
from combat.engine.items import use_item
from combat.engine.narration import render_event, render_status_apply
from combat.engine.effects import apply_status
from combat.loaders.abilities_loader import load_abilities
from combat.loaders.items_loader import load_items
from combat.loaders.status_effects_loader import load_status_effects
from combat.loaders.narration_loader import load_narration


def main():
    data_root = Path(__file__).parents[1] / "combat" / "data"
    abilities = load_abilities(data_root / "abilities.yaml")
    items = load_items(data_root / "items.yaml")
    status_cfg = load_status_effects(data_root / "status_effects.yaml")
    narr = load_narration(data_root / "narration.yaml")

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
    # give items
    a.inventory = {"healing_potion": 1, "fire_bomb": 1}
    b.inventory = {"cleansing_draught": 1}

    enc = Encounter([a, b], seed=4242)

    def ab(aid):
        return next((x for x in abilities.get("abilities", []) if x.get("id") == aid), None)

    provoke = ab("provoke")
    basic = ab("basic_attack")

    print("\n-- Round 1 --")
    # A uses Guard (apply guarding status)
    apply_status(a, "guarding", status_cfg, source_id=a.id)
    print("•", render_status_apply(a.name, "guarding", status_cfg, narr, enc.rng))
    # B uses Provoke on A
    evs = execute_ability(enc.participants, b, provoke, [a.id], enc.rng).events or []
    for ev in evs:
        if ev["type"] == "effect":
            print("•", render_status_apply(a.name, "taunted", status_cfg, narr, enc.rng))

    print("\n-- Round 2 --")
    # A (taunted) attacks; target auto-steers to taunter (B)
    evs = execute_ability(enc.participants, a, basic, [], enc.rng).events or []
    for ev in evs:
        if ev["type"] in ("hit", "miss"):
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
        elif ev["type"] == "guard_block":
            print("• Block reduces", ev["reduced"])

    print("\n-- Round 3 --")
    # B throws a fire bomb at A; A's guard might be consumed already
    fb = items.get("items", {}).get("fire_bomb")
    if fb:
        fb["id"] = "fire_bomb"
        result = use_item(enc.participants, b, fb, [a.id], enc.rng)
        evs = result.get("events", [])
        for ev in evs:
            if ev["type"] == "hit":
                print(f"• Fire Bomb hits {a.name} for {ev['amount']}")
            elif ev["type"] == "guard_block":
                print("• Block reduces", ev["reduced"])

    print("\n-- Round 4 --")
    # A uses healing potion
    hp = items.get("items", {}).get("healing_potion")
    if hp:
        hp["id"] = "healing_potion"
        result = use_item(enc.participants, a, hp, [a.id], enc.rng)
        evs = result.get("events", [])
        for ev in evs:
            if ev["type"] == "heal":
                print(f"• {a.name} heals {ev['amount']}")

    print(
        f"\nFinal → {a.name}: HP {a.hp:.1f}, Mana {a.mana:.1f} | {b.name}: HP {b.hp:.1f}, Mana {b.mana:.1f}"
    )


if __name__ == "__main__":
    main()
