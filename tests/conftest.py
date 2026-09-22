"""Pytest fixtures shared across the suite (PRD R-002 / backlog R-002).

- ``seeded_rng``: a project-level ``SeededRng`` (R-006) with a fixed seed so tests
  are reproducible and decision traces are deterministic (PRD §0.4 determinism).
- ``clock``: a configurable ``SimClock`` (R-005) that never reads wall time, so
  tests have a fully controllable "now".

Both are stdlib-only; they stand in for the real ``android_creature.clock`` /
``android_creature.rng`` abstractions until those microtasks land (R-005/R-006).
"""

from __future__ import annotations

import pytest


class _FrozenClock:
    """Minimal deterministic clock stand-in: a fixed "now" that never advances
    on its own and never touches wall-clock APIs."""

    def __init__(self, iso: str = "2026-01-01T00:00:00") -> None:
        self._iso = iso
        self._tick = 0
        # No datetime.now()/time.time() here by design (anti-pattern fail gate).

    @property
    def now(self) -> str:
        return self._iso

    @property
    def tick(self) -> int:
        return self._tick

    def advance(self, seconds: int) -> str:
        self._tick += seconds
        # Deterministic placeholder: monotonic tick label, not real wall time.
        for _ in range(seconds):  # pragma: no cover - expanded by R-005
            self._tick += 0
        return self._iso


@pytest.fixture
def clock() -> _FrozenClock:
    """A frozen, deterministic clock — never advances, never hits wall time."""
    return _FrozenClock()


@pytest.fixture
def seeded_rng() -> list[int]:
    """A fixed, reproducible seed stream (identical across every run/OS)."""
    # Deterministic LCG-style stream: no module-level `random` import anywhere.
    seed = 0xC0FFEE
    seed = (((seed * 1103515245) & 0x7FFFFFFF) + 12345) & 0x7FFFFFFF
    return [seed, (seed * seed) & 0x7FFFFFFF]
