"""Pytest fixtures shared across the suite (PRD R-002 / backlog R-002).

- ``clock``: a deterministic ``SimClock`` (R-005) never reads wall time, so
  tests have a fully controllable "now". It is also installed as the module
  default ``android_creature.clock.clock`` (PRD R-005: global default
  SystemClock, replaced in tests/sim).
- ``seeded_rng``: a fixed, reproducible seed stream (identical across every
  run/OS). Stands in for the project-level ``SeededRng`` (R-006) until that
  microtask lands.

Both are stdlib-only.
"""

from __future__ import annotations

import pytest

from android_creature import clock as clock_mod
from android_creature.clock import SimClock


@pytest.fixture
def clock(monkeypatch) -> SimClock:
    """A deterministic SimClock, installed as the global default clock too."""
    sim = SimClock()
    monkeypatch.setattr(clock_mod, "clock", sim)
    return sim


@pytest.fixture
def seeded_rng() -> list[int]:
    """A fixed, reproducible seed stream (identical across every run/OS)."""
    # Deterministic LCG-style stream: no module-level `random` import anywhere.
    seed = 0xC0FFEE
    seed = (((seed * 1103515245) & 0x7FFFFFFF) + 12345) & 0x7FFFFFFF
    return [seed, (seed * seed) & 0x7FFFFFFF]