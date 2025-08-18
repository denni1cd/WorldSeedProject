from __future__ import annotations
from combat.engine.rng import RandomSource
from combat.engine.narration import render_event

NARR = {
    "verbs": {"slash": ["slashes", "cleaves", "carves", "hews", "rends"]},
    "adjectives": {"fire": ["scorching", "blazing", "searing", "licking"]},
    "miss": [
        "{actor} lunges, but {target} slips aside.",
        "{actor}'s swing whistles past {target}.",
    ],
    "templates": {
        "physical_hit": [
            {
                "text": "{actor} {verb_slash} {target}'s {body_part} for {amount} {dtype}.",
                "weight": 3,
            }
        ],
        "physical_crit": [
            {
                "text": "Critical! {actor}'s blade bites deep—{amount} {dtype} to {target}'s {body_part}.",
                "weight": 2,
            }
        ],
        "fire_hit": [
            {
                "text": "{target} takes {amount} {adj_fire} damage as flames lick their {body_part}.",
                "weight": 3,
            }
        ],
    },
}


def test_variety_in_physical_lines():
    rng = RandomSource(seed=42)
    uniq = set()
    # synthesize 30 different contexts with varying parts/verbs
    parts = ["arm", "shoulder", "chest", "ribs", "gut", "thigh", "knee", "shin", "foot", "head"]
    for i in range(50):
        ctx = {
            "actor": "A",
            "target": "B",
            "hit": True,
            "crit": False,
            "amount": 7.5 + (i % 3),
            "dtype": "slashing",
            "body_part": rng.choice(parts),
        }
        s = render_event(ctx, NARR, rng)
        if "slashes" in s or "cleaves" in s or "carves" in s or "hews" in s or "rends" in s:
            uniq.add(s)
        if len(uniq) >= 6:
            break
    assert len(uniq) >= 6
