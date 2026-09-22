# Sprint 01 — M0: Repository / Architecture

- Status: `COMPLETE` (2026-09-22)
- Objective: Repositori skeleton, package Python, toolchain, config, logging, clock, RNG, errors, docs/ADR, Makefile.
- Entry criteria: Repo kosong tersedia (hanya dokumen). PRD + status sudah ada.
- Spec task: `docs/PRD.md` §O (M0) · Checklist master: `docs/backlog.md`

## Tasks

- [x] **R-001 — Initialize monorepo skeleton**
- [x] **R-002 — Python package skeleton + toolchain**
- [x] **R-003 — Config system**
- [x] **R-004 — Structured logging**
- [x] **R-005 — Clock abstraction**
- [x] **R-006 — Seeded RNG utility**
- [x] **R-007 — Error taxonomy**
- [x] **R-008 — Docs skeleton + ADRs**
- [x] **R-009 — Dev runner + lint gates**

## Exit criteria (SEMUA harus terpenuhi sebelum sprint ditandai COMPLETE)

- [x] make setup && make test hijau tanpa device & tanpa network
- [x] creature --version / pokedex --version exit 0; creature config validate exit 0; konfig invalid exit 5
- [x] Grep gate wall-clock lolos (tidak ada datetime.now()/time.time() di luar boundary adapter)
- [x] docs/PRD.md + ADR-001..008 ter-commit; commit pertama bersih
- [x] Gate lint/coverage terdefinisi di Makefile (enforcement 85% mulai M6)

## Catatan sesi / keputusan sprint ini

- R-005 (2026-09-22): conftest `_FrozenClock` diganti `SimClock` sungguhan (global default `clock` di-replace di tests). Hygiene banned-API: tidak ada `datetime.now`/`time.time` di seluruh `src/` (adapter memakai `monotonic`/`gmtime`).
- R-006 (2026-09-22): conftest `seeded_rng` placeholder LCG diganti `SeededRng(0xC0FFEE)`; source `src/` bebas token `random.` (grep gate tetap CLEAN).
- R-007 (2026-09-22): `ConfigError` dikonsolidasi ke `errors.py`; `config.ConfigError` jadi alias.
- R-009 (2026-09-22): Makefile (setup/test/test-hw/lint/record-fixture), `scripts/setup.sh`, `tests/README.md`, `scripts/check_src_hygiene.py` (token banned + import stdlib-only). Coverage target 85% didefer ke M6 (sesuai exit criteria).
