from __future__ import annotations
import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class RandomSource:
    """Seedable RNG facade for deterministic combat."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def randf(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        # Coerce to list so generators/sets are safe
        return self._rng.choice(list(seq))

    # NEW: state get/set for snapshot/restore
    def get_state(self):
        return self._rng.getstate()

    def set_state(self, state) -> None:
        self._rng.setstate(state)
