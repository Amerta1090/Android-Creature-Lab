"""Seeded RNG utility (PRD R-006) — deterministic randomness.

Every random draw a creature makes goes through :class:`SeededRng`; this module
is the **single import surface** for randomness (R-006 DoD). The stdlib
``Random`` class is seeded with a fixed integer, so a given (seed, tick) always
produces the identical stream — reproducible across runs and processes
(int seeds, unlike strings, are not affected by hash randomization).

Surface:

- ``SeededRng(seed, tick=0)``   one RNG per creature.
- ``rand_float(a=0.0, b=1.0)``  uniform float in ``[a, b]`` (either order).
- ``choice(weighted)``          pick one ``(value, weight)`` by weight;
                                positive total weight required.
- ``set_tick(tick)``            reseed for **per-tick stability**: the same
                                seed at the same tick always replays the same
                                stream, and a new tick starts a fresh
                                deterministic stream.

Seeds are mixed with the tick numerically (``seed`` in the high bits, ``tick``
in the low 32), so seed and tick choices never collide and every (seed, tick)
pair is deterministic.

There is no ``random``-module API call anywhere in ``src`` (the grep gate
stays clean): draws go through ``Random.uniform``, and module-level ``random``
functions are never used.
"""

from __future__ import annotations

from random import Random
from typing import Sequence, TypeVar, Tuple

T = TypeVar("T")

#: Low 32-bit mask used when mixing tick into the seed.
_TICK_MASK = 0xFFFFFFFF


def _mix(seed: int, tick: int) -> int:
    """Byte-level deterministic mix: seed in high bits, tick in the low 32."""
    return (seed << 32) ^ (tick & _TICK_MASK)


class SeededRng:
    """A creature's deterministic RNG, reseeded per tick.

    Instances with the same ``(seed, tick)`` replay identical streams; two
    creatures with different seeds never see the same stream.
    """

    def __init__(self, seed: int, tick: int = 0) -> None:
        self._seed = seed
        self._tick = tick
        self._rebuild()

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def tick(self) -> int:
        return self._tick

    def set_tick(self, tick: int) -> None:
        """Reseed for a new tick: same seed+tick ⇒ same stream (stability)."""
        self._tick = tick
        self._rebuild()

    def _rebuild(self) -> None:
        self._rng = Random(_mix(self._seed, self._tick))

    def rand_float(self, a: float = 0.0, b: float = 1.0) -> float:
        """Uniform float in ``[a, b]`` (works with either ordering)."""
        return self._rng.uniform(a, b)

    def choice(self, weighted: Sequence[Tuple[T, float]]) -> T:
        """Weighted pick: returns one value from ``(value, weight)`` pairs.

        Weights must be non-negative with a positive total; a zero weight never
        wins. Bounds are exact (``target <= cumulative``), so a float-tolerance
        fallback is never needed.
        """
        if any(weight < 0 for _, weight in weighted):
            raise ValueError(
                f"choice: weights must be non-negative, got {weighted!r}"
            )
        total = sum(weight for _, weight in weighted)
        if total <= 0:
            raise ValueError(f"choice: total weight must be positive, got {total!r}")
        target = self._rng.uniform(0.0, total)
        cumulative = 0.0
        for value, weight in weighted:
            cumulative += weight
            if target <= cumulative:
                return value
        return weighted[-1][0]  # pragma: no cover - unreachable (target < total)