from __future__ import annotations
from typing import Dict, Any
from .rng import RandomSource


def _pick(pool):
    return pool[0] if not pool else pool[0]


def render_event(
    ctx: Dict[str, Any],
    narration_cfg: Dict[str, Any],
    rng: RandomSource,
) -> str:
    """
    ctx keys: actor, target, hit(bool), crit(bool), amount(float), dtype(str), body_part(str)
    narration_cfg: { templates, verbs, adjectives, miss }
    """
    actor = ctx.get("actor", "Actor")
    target = ctx.get("target", "Target")
    amount = ctx.get("amount", 0.0)
    dtype = ctx.get("dtype", "damage")
    body_part = ctx.get("body_part", "body")
    hit = bool(ctx.get("hit", False))
    crit = bool(ctx.get("crit", False))

    verbs = narration_cfg.get("verbs", {})
    adjs = narration_cfg.get("adjectives", {})
    miss_pool = narration_cfg.get("miss", [])
    tmpls = narration_cfg.get("templates", {})

    def choice(lst):
        return rng.choice(lst) if lst else ""

    def weight_choice(items):
        # items: list of dicts with {weight, text} OR a dict mapping → normalize to list
        if isinstance(items, dict):
            flat = []
            for k, v in items.items():
                if isinstance(v, dict) and "text" in v:
                    flat.append({"text": v["text"], "weight": v.get("weight", 1)})
            items = flat
        if not items:
            return ""
        total = sum(max(1, int(it.get("weight", 1))) for it in items)
        r = rng.randint(1, total)
        acc = 0
        for it in items:
            acc += max(1, int(it.get("weight", 1)))
            if r <= acc:
                return it.get("text", "")
        return items[-1].get("text", "")

    if not hit:
        return choice(miss_pool).format(actor=actor, target=target)

    # Template routing
    key = None
    if dtype == "fire":
        key = "fire_hit"
    elif crit:
        key = "physical_crit"
    else:
        key = "physical_hit"

    # normalize templates into a list of {text, weight}
    tpl_entry = tmpls.get(key)
    tpl_list = []
    if isinstance(tpl_entry, dict) and "text" in tpl_entry:
        tpl_list = [tpl_entry]
    elif isinstance(tpl_entry, list):
        tpl_list = tpl_entry

    template = (
        weight_choice(tpl_list) if tpl_list else "{actor} hits {target} for {amount} {dtype}."
    )

    tokens = {
        "actor": actor,
        "target": target,
        "amount": (int(amount) if abs(amount - round(amount)) < 1e-6 else f"{amount:.1f}"),
        "dtype": dtype,
        "body_part": body_part,
        "verb_slash": choice(verbs.get("slash", [])),
        "adj_fire": choice(adjs.get("fire", [])),
    }
    return template.format(**tokens)
