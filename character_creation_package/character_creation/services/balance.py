from __future__ import annotations

from typing import Dict, Any


DEFAULT_PROFILE = {
    "hp_scale": 1.0,
    "mana_scale": 1.0,
    "regen_amount_scale": 1.0,
    "status_effect_scale": 1.0,
    "xp_gain_scale": 1.0,
    "xp_cost_scale": 1.0,
}


def current_profile(balance_cfg: Dict[str, Any]) -> Dict[str, float]:
    if not balance_cfg:
        return DEFAULT_PROFILE.copy()
    cur = balance_cfg.get("current", "normal")
    table = balance_cfg.get("difficulties", {}) or {}
    prof = dict(DEFAULT_PROFILE)
    prof.update(table.get(cur, {}))
    return prof
