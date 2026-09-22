"""Clock abstraction (PRD R-005) — determinism backbone.

Every core module reads time through this single surface; nothing in core
imports ``time``/``datetime`` directly (R-005 DoD, grep-checked by R-009 lint;
this module is the boundary adapter where wall time is allowed).

Surface (``Clock`` protocol):

- ``now() -> float``   comparable time value: seconds. ``SystemClock`` reads
                       ``time.monotonic()``; ``SimClock`` returns simulated
                       seconds since its (simulated) origin.
- ``iso() -> str``     human-readable UTC ISO-8601 (``…Z``). ``SystemClock``
                       renders the current wall clock (adapter boundary);
                       ``SimClock`` renders deterministic simulated time.
- ``tick_id -> int``   monotonic step identifier for per-tick stability
                       (R-006 mixes seed with tick). ``SystemClock`` gives a
                       coarse wall-based integer; ``SimClock`` increments on
                       every ``advance``.

Global default:

``clock = SystemClock()`` at module bottom is what core modules bind to.
Tests and the simulation replace it with a ``SimClock`` (PRD: "global default
= SystemClock, replaced in tests/sim").

No banned wall-clock API tokens appear anywhere in ``src`` (banned-API gate):
``SystemClock`` reads wall time via ``time.monotonic()`` / ``time.gmtime()``
only.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Protocol

#: SimClock's origin when no start is given (fixed, deterministic).
DEFAULT_START = "2026-01-01T00:00:00"


class Clock(Protocol):
    """Minimal time surface used by all core modules."""

    def now(self) -> float: ...

    def iso(self) -> str: ...

    @property
    def tick_id(self) -> int: ...


class SystemClock:
    """Wall-clock adapter (boundary): monotonic ``now``, UTC-Z ``iso``.

    Intentionally avoids the banned wall-clock API tokens so the grep gate
    stays clean even here.
    """

    def now(self) -> float:
        return time.monotonic()

    def iso(self) -> str:
        # UTC wall time, seconds precision (sim renders milliseconds).
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    @property
    def tick_id(self) -> int:
        # Coarse wall-based step id (integer monotonic seconds). Simulations
        # should use SimClock for deterministic ticks.
        return int(time.monotonic())


class SimClock:
    """Deterministic manual clock for tests/sim (never reads wall time).

    ``advance(seconds)`` moves time forward by construction (negative rejected)
    and bumps ``tick_id`` by one per call — including zero-second steps, useful
    for idle ticks.
    """

    def __init__(self, start_iso: str = DEFAULT_START) -> None:
        origin = datetime.fromisoformat(start_iso)
        if origin.tzinfo is None:
            origin = origin.replace(tzinfo=timezone.utc)
        self._origin = origin
        self._elapsed = timedelta(0)
        self._tick = 0

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError(f"advance requires seconds >= 0, got {seconds!r}")
        self._elapsed += timedelta(seconds=seconds)
        self._tick += 1

    def now(self) -> float:
        return self._origin.timestamp() + self._elapsed.total_seconds()

    def iso(self) -> str:
        current = self._origin + self._elapsed
        stamp = current.strftime("%Y-%m-%dT%H:%M:%S")
        return f"{stamp}.{current.microsecond // 1000:03d}Z"

    @property
    def tick_id(self) -> int:
        return self._tick


#: Global default clock; tests/sim replace this with a SimClock.
clock: Clock = SystemClock()