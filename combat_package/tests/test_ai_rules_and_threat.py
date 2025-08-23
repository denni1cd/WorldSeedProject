from __future__ import annotations
from pathlib import Path
from combat.engine.combatant import Combatant
from combat.engine.encounter import Encounter
from combat.engine.ai import choose_and_execute
from combat.engine.threat import add_threat
from combat.loaders.abilities_loader import load_abilities
from combat.loaders.ai_rules_loader import load_ai_rules
from combat.engine.rng import RandomSource


def _load():
    data_root = Path(__file__).parents[1] / "combat" / "data"
    return load_abilities(data_root / "abilities.yaml"), load_ai_rules(data_root / "ai_rules.yaml")


def test_ai_picks_guard_when_low_hp():
    abilities, rules = _load()
    a = Combatant("A", "A", {"DEX": 7}, hp=10.0, mana=6.0, resist={}, tags=["humanoid"], team="t1")
    b = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=12.0, resist={}, tags=["humanoid"], team="t2")
    enc = Encounter([a, b], seed=1)
    out = choose_and_execute(enc.participants, a, abilities, rules, enc.threat, RandomSource(1))
    assert out["ok"] and out["ability_id"] == "guard"


def test_ai_prefers_fireball_when_mana_ready_else_basic():
    abilities, rules = _load()
    a = Combatant(
        "A", "A", {"INT": 12, "DEX": 7}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t1"
    )
    b = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t2")
    enc = Encounter([a, b], seed=2)
    out1 = choose_and_execute(enc.participants, a, abilities, rules, enc.threat, RandomSource(2))
    assert out1["ok"] and out1["ability_id"] in ("fireball", "provoke", "basic_attack")
    # Spend A's mana so fireball not ready next
    a.mana = 0.0
    out2 = choose_and_execute(enc.participants, a, abilities, rules, enc.threat, RandomSource(3))
    assert out2["ok"] and out2["ability_id"] in ("provoke", "basic_attack")


def test_threat_steers_target_choice():
    abilities, rules = _load()
    a = Combatant(
        "A", "A", {"ATT": 8, "DEX": 7}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t1"
    )
    b = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t2")
    c = Combatant("C", "C", {"DEX": 6}, hp=20.0, mana=0.0, resist={}, tags=["humanoid"], team="t2")
    enc = Encounter([a, b, c], seed=3)
    # From A's perspective (victim is A), make B far more threatening than C
    add_threat(enc.threat, "A", "B", 50.0)
    out = choose_and_execute(enc.participants, a, abilities, rules, enc.threat, RandomSource(4))
    # A should pick highest_threat (B) as target for first matching offensive rule
    assert out["ok"] and out["target_ids"] and out["target_ids"][0] == "B"


def test_ai_determinism_under_seed():
    abilities, rules = _load()
    a = Combatant("A", "A", {"DEX": 7}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t1")
    b = Combatant("B", "B", {"DEX": 6}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t2")
    enc1 = Encounter([a, b], seed=5)
    enc2 = Encounter(
        [
            Combatant(
                "A", "A", {"DEX": 7}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t1"
            ),
            Combatant(
                "B", "B", {"DEX": 6}, hp=20.0, mana=6.0, resist={}, tags=["humanoid"], team="t2"
            ),
        ],
        seed=5,
    )
    out1 = choose_and_execute(
        enc1.participants, enc1.next_turn(), abilities, rules, enc1.threat, enc1.rng
    )
    out2 = choose_and_execute(
        enc2.participants, enc2.next_turn(), abilities, rules, enc2.threat, enc2.rng
    )
    assert out1["ability_id"] == out2["ability_id"] and out1["target_ids"] == out2["target_ids"]
