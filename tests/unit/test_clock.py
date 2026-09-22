"""Unit tests — R-005 Clock abstraction (PRD §R-005).

Covers: ``Clock`` protocol surface (now/iso/tick_id); ``SystemClock`` adapter
(monotonic now, UTC-Z iso, coarse tick) as the module default; ``SimClock``
(manual ``advance``, monotonic by construction, deterministic iso/indexing);
module-global ``clock`` replacement for tests/sim; wall-clock hygiene — the
banned API tokens (``datetime.now`` / ``time.time``) appear nowhere in ``src``,
and only the boundary adapter imports time/datetime (PRD NFR-2 / R-005 DoD,
formalized as the R-009 lint gate).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

import android_creature
from android_creature import clock as clock_mod

_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$")

ORIGIN_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()


# --------------------------------------------------------------------------- #
# default + protocol surface
# --------------------------------------------------------------------------- #

def test_default_clock_is_system() -> None:
    assert isinstance(clock_mod.clock, clock_mod.SystemClock)


def test_system_now_is_monotonic_float() -> None:
    c = clock_mod.SystemClock()
    a, b = c.now(), c.now()
    assert isinstance(a, float)
    assert b >= a  # monotonic (non-decreasing)


def test_system_iso_is_utc_z_shape() -> None:
    iso = clock_mod.SystemClock().iso()
    assert _ISO_Z.match(iso) is not None, f"bad iso shape: {iso!r}"
    assert iso.endswith("Z")


def test_system_tick_id_is_int() -> None:
    tick = clock_mod.SystemClock().tick_id
    assert isinstance(tick, int)


# --------------------------------------------------------------------------- #
# SimClock
# --------------------------------------------------------------------------- #

def test_sim_initial_iso_default_start() -> None:
    assert clock_mod.SimClock().iso() == "2026-01-01T00:00:00.000Z"


def test_sim_custom_start_iso() -> None:
    sim = clock_mod.SimClock("2026-03-04T05:06:07")
    assert sim.iso() == "2026-03-04T05:06:07.000Z"


def test_sim_tick_begins_at_zero() -> None:
    assert clock_mod.SimClock().tick_id == 0


def test_sim_advance_moves_now_and_iso() -> None:
    sim = clock_mod.SimClock()
    sim.advance(1.5)
    assert sim.now() == pytest.approx(ORIGIN_EPOCH + 1.5)
    assert sim.iso() == "2026-01-01T00:00:01.500Z"


def test_sim_advance_chained_is_monotonic_and_ticks() -> None:
    sim = clock_mod.SimClock()
    previous = sim.now()
    for step in (0.25, 10.0, 60.0):
        sim.advance(step)
        now = sim.now()
        assert now > previous
        assert sim.iso() == pytest.approx(_iso_of(now))
        previous = now
    assert sim.tick_id == 3


def test_sim_zero_advance_ticks_without_moving_time() -> None:
    sim = clock_mod.SimClock()
    before = sim.now()
    sim.advance(0.0)
    assert sim.now() == before
    assert sim.tick_id == 1


def test_sim_now_iso_consistency_after_big_advance() -> None:
    sim = clock_mod.SimClock()
    sim.advance(3600.25)
    assert sim.iso() == "2026-01-01T01:00:00.250Z"
    assert sim.now() == pytest.approx(ORIGIN_EPOCH + 3600.25)


def test_sim_negative_advance_rejected() -> None:
    sim = clock_mod.SimClock()
    with pytest.raises(ValueError):
        sim.advance(-1)


# --------------------------------------------------------------------------- #
# global clock replacement (tests/sim)
# --------------------------------------------------------------------------- #

def test_module_clock_replacable_by_sim(monkeypatch) -> None:
    sim = clock_mod.SimClock("2025-12-31T23:59:59")
    monkeypatch.setattr(clock_mod, "clock", sim)
    assert clock_mod.clock is sim
    assert clock_mod.clock.iso() == "2025-12-31T23:59:59.000Z"
    clock_mod.clock.advance(1)
    assert clock_mod.clock.iso() == "2026-01-01T00:00:00.000Z"


# --------------------------------------------------------------------------- #
# wall-clock hygiene (R-005 DoD / R-009 lint preview)
# --------------------------------------------------------------------------- #

def _src_files() -> list[Path]:
    root = Path(android_creature.__file__).resolve().parent
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def test_clock_adapter_avoids_banned_api_tokens() -> None:
    source = Path(clock_mod.__file__).read_text(encoding="utf-8")
    assert "datetime.now" not in source
    assert "time.time" not in source


def test_only_clock_adapter_imports_time_datetime() -> None:
    offenders = []
    for path in _src_files():
        if path.name == "clock.py":
            continue
        source = path.read_text(encoding="utf-8")
        for banned in ("import time", "import datetime", "from datetime"):
            if banned in source:
                offenders.append(f"{path.name}: {banned}")
    assert offenders == []


def _iso_of(epoch: float) -> str:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{dt.microsecond // 1000:03d}Z"