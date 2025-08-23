from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.items import use_item
from combat.loaders.items_loader import load_items
from combat.engine.rng import RandomSource


def _items():
    return load_items(Path(__file__).parents[1] / "combat" / "data" / "items.yaml").get("items", {})


def test_healing_and_bomb_flow():
    items = _items()
    a = Combatant(
        "A",
        "A",
        {"INT": 8, "DEX": 5},
        hp=10.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t1",
    )
    b = Combatant(
        "B",
        "B",
        {"INT": 10, "DEX": 15},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t2",
    )
    a.inventory = {"healing_potion": 1}
    b.inventory = {"fire_bomb": 1}
    # heal self
    hp = dict(items["healing_potion"])
    hp["id"] = "healing_potion"
    r1 = use_item([a, b], a, hp, [a.id], RandomSource(1))
    assert r1["ok"]
    assert a.hp > 10.0
    assert a.inventory["healing_potion"] == 0
    # bomb enemy
    fb = dict(items["fire_bomb"])
    fb["id"] = "fire_bomb"
    r2 = use_item([a, b], b, fb, [a.id], RandomSource(1))  # Use seed 1 for more reliable hit
    print(f"Fire bomb result: {r2}")
    print(f"Fire bomb events: {r2['events']}")
    assert r2["ok"]
    hits = [ev for ev in r2["events"] if ev["type"] == "hit"]
    assert hits and a.hp < 22.0  # took damage


def test_cleanse_removes_burning():
    from combat.engine.effects import apply_status
    from combat.loaders.status_effects_loader import load_status_effects

    status_cfg = load_status_effects(
        Path(__file__).parents[1] / "combat" / "data" / "status_effects.yaml"
    )
    items = _items()
    v = Combatant(
        "V",
        "Victim",
        {"INT": 10},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t1",
    )
    apply_status(v, "burning", status_cfg, source_id="S")
    assert any(s["id"] == "burning" for s in v.statuses)
    v.inventory = {"cleansing_draught": 1}
    cd = dict(items["cleansing_draught"])
    cd["id"] = "cleansing_draught"
    r = use_item([v], v, cd, [v.id], RandomSource(5))
    assert r["ok"]
    assert not any(s["id"] == "burning" for s in v.statuses)
