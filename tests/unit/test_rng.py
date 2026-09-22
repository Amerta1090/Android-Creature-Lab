"""Unit tests — R-006 Seeded RNG utility (PRD §R-006).

Covers: same seed ⇒ same stream; different seeds vary; ``rand_float`` bounds
(default unit interval and arbitrary intervals); ``choice`` weighted bounds
(zero/negative/single/all-zero cases); per-tick stability (``set_tick`` — same
seed+tick ⇒ identical stream, different tick ⇒ different stream, reset works);
module-level ``random`` leakage guard (only ``rng.py`` imports it, no
``random.`` API calls anywhere in ``src`` — PRD R-006 DoD / R-009 lint).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import android_creature
from android_creature import rng as rng_mod
from android_creature.rng import SeededRng


# --------------------------------------------------------------------------- #
# reproducibility
# --------------------------------------------------------------------------- #

def test_same_seed_same_stream() -> None:
    a = SeededRng(42)
    b = SeededRng(42)
    assert [a.rand_float() for _ in range(20)] == [b.rand_float() for _ in range(20)]


def test_different_seeds_vary() -> None:
    a = [SeededRng(1).rand_float() for _ in range(20)]
    b = [SeededRng(2).rand_float() for _ in range(20)]
    assert a != b


# --------------------------------------------------------------------------- #
# rand_float
# --------------------------------------------------------------------------- #

def test_rand_float_default_is_unit_interval() -> None:
    rng = SeededRng(7)
    values = [rng.rand_float() for _ in range(200)]
    assert all(0.0 <= v <= 1.0 for v in values)
    assert len(set(values)) > 1  # actually varies


def test_rand_float_bounds_respected() -> None:
    rng = SeededRng(7)
    values = [rng.rand_float(2.0, 5.0) for _ in range(200)]
    assert all(2.0 <= v <= 5.0 for v in values)
    assert len(set(values)) > 1


def test_rand_float_reversed_bounds_same_interval() -> None:
    rng = SeededRng(7)
    values = [rng.rand_float(5.0, 2.0) for _ in range(200)]
    assert all(2.0 <= v <= 5.0 for v in values)


# --------------------------------------------------------------------------- #
# choice (weighted)
# --------------------------------------------------------------------------- #

def test_choice_positive_weight_always_wins() -> None:
    rng = SeededRng(11)
    for _ in range(200):
        assert rng.choice([("a", 0), ("b", 1), ("c", 0)]) == "b"


def test_choice_never_picks_zero_weight() -> None:
    rng = SeededRng(11)
    picked = {rng.choice([("a", 1), ("b", 0), ("c", 0)]) for _ in range(300)}
    assert picked == {"a"}


def test_choice_respects_relative_weights() -> None:
    rng = SeededRng(11)
    counts = {"a": 0, "b": 0}
    for _ in range(500):
        counts[rng.choice([("a", 1), ("b", 99)])] += 1
    assert counts["a"] > 0 and counts["b"] > 0
    assert counts["b"] > counts["a"]  # heavy weight dominates


def test_choice_single_option_always() -> None:
    rng = SeededRng(13)
    assert rng.choice([("only", 5)]) == "only"


def test_choice_all_zero_weights_rejected() -> None:
    rng = SeededRng(13)
    with pytest.raises(ValueError):
        rng.choice([("a", 0), ("b", 0)])


def test_choice_negative_weight_rejected() -> None:
    rng = SeededRng(13)
    with pytest.raises(ValueError):
        rng.choice([("a", -1), ("b", 2)])


# --------------------------------------------------------------------------- #
# per-tick stability
# --------------------------------------------------------------------------- #

def test_same_seed_same_tick_stable_across_instances() -> None:
    a, b = SeededRng(99, tick=3), SeededRng(99, tick=3)
    assert [a.rand_float() for _ in range(15)] == [b.rand_float() for _ in range(15)]


def test_different_tick_varies() -> None:
    tick1 = [SeededRng(99, tick=1).rand_float() for _ in range(15)]
    tick2 = [SeededRng(99, tick=2).rand_float() for _ in range(15)]
    assert tick1 != tick2


def test_set_tick_resets_stream_to_that_tick() -> None:
    fresh = SeededRng(5, tick=7)
    expected = [fresh.rand_float() for _ in range(10)]

    rng = SeededRng(5, tick=0)
    rng.rand_float(), rng.rand_float()  # burn draws at a different tick
    rng.set_tick(7)
    assert [rng.rand_float() for _ in range(10)] == expected


def test_set_tick_changes_stream() -> None:
    rng = SeededRng(5, tick=0)
    before = [rng.rand_float() for _ in range(10)]
    rng.set_tick(1)
    after = [rng.rand_float() for _ in range(10)]
    assert before != after


# --------------------------------------------------------------------------- #
# global default fixture + hygiene
# --------------------------------------------------------------------------- #

def test_seeded_rng_fixture_is_seeded_and_deterministic(seeded_rng) -> None:
    assert isinstance(seeded_rng, SeededRng)
    twin = SeededRng(0xC0FFEE)
    assert [seeded_rng.rand_float() for _ in range(10)] == [
        twin.rand_float() for _ in range(10)
    ]


def _src_files() -> list[Path]:
    root = Path(android_creature.__file__).resolve().parent
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def test_only_rng_module_imports_random() -> None:
    offenders = []
    for path in _src_files():
        if path.name == "rng.py":
            continue
        source = path.read_text(encoding="utf-8")
        for banned in ("import random", "from random"):
            if banned in source:
                offenders.append(f"{path.name}: {banned}")
    assert offenders == []


def test_no_module_level_random_api_in_src() -> None:
    for path in _src_files():
        source = path.read_text(encoding="utf-8")
        assert "random." not in source, f"{path.name} uses a random.* call"