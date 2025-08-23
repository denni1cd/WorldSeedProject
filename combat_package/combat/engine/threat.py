from __future__ import annotations
from typing import Dict, List


def blank_table(participant_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Threat is stored PER-VICTIM: T[victim_id][attacker_id] = score
    Higher score means the victim is more likely to target that attacker.
    """
    return {vid: {} for vid in participant_ids}


def add_threat(
    table: Dict[str, Dict[str, float]], victim_id: str, attacker_id: str, amount: float
) -> None:
    if victim_id not in table:
        table[victim_id] = {}
    table[victim_id][attacker_id] = table[victim_id].get(attacker_id, 0.0) + float(amount)


def decay_all(table: Dict[str, Dict[str, float]], factor: float = 0.9) -> None:
    # Optional: keep values bounded; factor in [0..1]
    for v in list(table.keys()):
        for a in list(table[v].keys()):
            table[v][a] *= float(factor)


def highest_threat_target(
    table: Dict[str, Dict[str, float]], victim_id: str, candidates: List[str]
) -> str | None:
    scores = table.get(victim_id, {})
    best, best_val = None, float("-inf")
    for cid in candidates:
        val = scores.get(cid, 0.0)
        if val > best_val:
            best, best_val = cid, val
    return best


def normalize(table: Dict[str, Dict[str, float]], cap: float = 9999.0) -> None:
    # Prevent runaway growth
    for v in table:
        for a in table[v]:
            if table[v][a] > cap:
                table[v][a] = cap
