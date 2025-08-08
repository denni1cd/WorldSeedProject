import random
from typing import Any, Sequence


def roll_normal(mean: float, sd: float) -> float:
    """
    Returns a random float from a normal distribution.
    """
    return random.gauss(mean, sd)


def roll_uniform(min_val: float, max_val: float) -> float:
    """
    Returns a random float from a uniform distribution.
    """
    return random.uniform(min_val, max_val)


def choice(seq: Sequence) -> Any:
    """
    Returns a random element from a non-empty sequence.
    Returns None if the sequence is empty.
    """
    if not seq:
        return None
    return random.choice(seq)
