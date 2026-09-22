"""Pytest fixtures shared across the suite (PRD R-002 / backlog R-002).

- ``clock``: a deterministic ``SimClock`` (R-005) never reads wall time, so
  tests have a fully controllable "now". It is also installed as the module
  default ``android_creature.clock.clock`` (PRD R-005: global default
  SystemClock, replaced in tests/sim).
- ``seeded_rng``: a project-level ``SeededRng`` (R-006) with a fixed seed so
  tests are reproducible and decision traces are deterministic (PRD §0.4).

Both are stdlib-only.
"""

from __future__ import annotations

import pytest

from android_creature import clock as clock_mod
from android_creature.clock import SimClock
from android_creature.rng import SeededRng


@pytest.fixture
def clock(monkeypatch) -> SimClock:
    """A deterministic SimClock, installed as the global default clock too."""
    sim = SimClock()
    monkeypatch.setattr(clock_mod, "clock", sim)
    return sim


@pytest.fixture
def seeded_rng() -> SeededRng:
    """A fixed-seed SeededRng (same seed every run, reproducible streams)."""
    return SeededRng(0xC0FFEE)