# Testing guide

How to run and structure the offline-first test suite (PRD §L / R-009).

## Commands

| Command | What it runs | Needs |
|---------|--------------|-------|
| `make setup` | Create `.venv` + editable install (`scripts/setup.sh`) | python3 only |
| `make test` | `pytest tests -m "not hw"` — unit + sim + adapter + regression, offline | nothing |
| `make test-hw` | `pytest -m hw` — hardware tests | attached device (`adb devices`) |
| `make lint` | `python -m compileall` + `scripts/check_src_hygiene.py` | nothing |
| `make record-fixture` | record adb fixtures for offline replay | wiring arrives with A-005 |
| `.venv/bin/pytest tests/unit -q` | a single tier directly | nothing |

Everything is **offline**: no network, no device (until `test-hw`). The suite
is deterministic — tests use the injected `SimClock` and `SeededRng` fixtures,
never wall clock / global randomness.

## Layout

```
tests/
  conftest.py        shared fixtures (clock, seeded_rng)
  smoke/             entry-point smoke tests (--version, exit codes)
  unit/              pure unit tests (config, logging, clock, rng, errors, …)
  sim/               simulation tests (creature/simulation milestones)   [M7+]
  adapter/           adapter tests against mocked/recorded adb          [M1+]
  regression/        golden-fixture regression tests                     [A-005+]
```

Tiers that don't exist yet are placeholder dirs (`.gitkeep`) so `make test`
collects them cleanly as milestones land — new tests go into the matching tier,
not into `tests/unit/`.

## Marker conventions

- `@pytest.mark.hw` = requires a real device; skipped by `make test`.
- No other markers are used today; keep the suite collection cheap.

## Fixtures

- `clock` — a `SimClock` installed as the global default
  (`android_creature.clock.clock`), so time-dependent code is controllable.
- `seeded_rng` — a fixed-seed `SeededRng(0xC0FFEE)`, reproducible streams.

## Determinism requirements

- Tests must not read wall time or global randomness (PRD NFR-2). If a test
  needs time, drive it through the `clock` fixture.
- Assertions compare structure/shape, not absolute timestamps, where the
  boundary renders time (e.g. logging lines).