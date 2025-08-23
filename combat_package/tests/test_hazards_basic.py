from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.loaders.hazards_loader import load_hazards
from combat.engine.narration import render_hazard_event


def _hz_cfg():
    return load_hazards(Path(__file__).parents[1] / "combat" / "data" / "hazards.yaml")


def test_lava_damages_non_flying_in_lava_location():
    a = Combatant(
        "A",
        "A",
        {"INT": 0},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid"],
        team="t1",
        location="lava",
    )
    b = Combatant(
        "B",
        "B",
        {"INT": 12},
        hp=20.0,
        mana=0.0,
        resist={},
        tags=["humanoid", "flying"],
        team="t2",
        location="lava",
    )
    enc = Encounter([a, b], seed=1)
    evs = enc.process_hazards("start_of_turn")
    # at least one hazard event for A; B is flying so should be skipped
    targets = [
        e["target_id"]
        for e in evs
        if e["type"] == "hazard" and e["hazard_id"] == "lava_zone" and e["kind"] == "damage"
    ]
    assert "A" in targets and "B" not in targets


def test_fountain_heals_end_of_turn():
    a = Combatant(
        "A", "A", {}, hp=10.0, mana=0.0, resist={}, tags=[], team="t1", location="fountain"
    )
    enc = Encounter([a], seed=2)
    evs = enc.process_hazards("end_of_turn")
    heals = [e for e in evs if e["hazard_id"] == "healing_fountain" and e["kind"] == "heal"]
    assert heals and heals[0]["amount"] > 0.0
    assert a.hp > 10.0


def test_hazard_narration_nonempty():
    hz = _hz_cfg()
    a = Combatant("A", "A", {}, hp=20.0, mana=0.0, resist={}, tags=[], team="t1", location="lava")
    enc = Encounter([a], seed=3)
    evs = enc.process_hazards("start_of_turn")
    lines = [render_hazard_event(e, hz, enc.rng) for e in evs]
    assert all(isinstance(x, str) and x for x in lines)


def test_hazard_determinism_same_seed():
    a1 = Combatant("A", "A", {}, hp=20.0, mana=0.0, resist={}, tags=[], team="t1", location="lava")
    a2 = Combatant("A", "A", {}, hp=20.0, mana=0.0, resist={}, tags=[], team="t1", location="lava")
    from combat.engine.encounter import Encounter

    e1 = Encounter([a1], seed=42)
    e2 = Encounter([a2], seed=42)
    evs1 = e1.process_hazards("start_of_turn")
    evs2 = e2.process_hazards("start_of_turn")

    # amounts & kinds should match
    def tpl(e):
        return (e["hazard_id"], e["target_id"], e["kind"], e.get("amount", 0))

    assert [tpl(x) for x in evs1] == [tpl(x) for x in evs2]
