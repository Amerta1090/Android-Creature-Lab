# Sprint 01 — M0: Repository / Architecture

- Status: `IN PROGRESS` (2026-09-22)
- Objective: Repositori skeleton, package Python, toolchain, config, logging, clock, RNG, errors, docs/ADR, Makefile.
- Entry criteria: Repo kosong tersedia (hanya dokumen). PRD + status sudah ada.
- Spec task: `docs/PRD.md` §O (M0) · Checklist master: `docs/backlog.md`

## Tasks

- [x] **R-001 — Initialize monorepo skeleton**
- [x] **R-002 — Python package skeleton + toolchain**
- [ ] **R-003 — Config system**
- [ ] **R-004 — Structured logging**
- [ ] **R-005 — Clock abstraction**
- [ ] **R-006 — Seeded RNG utility**
- [ ] **R-007 — Error taxonomy**
- [ ] **R-008 — Docs skeleton + ADRs**
- [ ] **R-009 — Dev runner + lint gates**

## Exit criteria (SEMUA harus terpenuhi sebelum sprint ditandai COMPLETE)

- [ ] make setup && make test hijau tanpa device & tanpa network
- [ ] creature --version / pokedex --version exit 0; creature config validate exit 0; konfig invalid exit 5
- [ ] Grep gate wall-clock lolos (tidak ada datetime.now()/time.time() di luar boundary adapter)
- [ ] docs/PRD.md + ADR-001..008 ter-commit; commit pertama bersih
- [ ] Gate lint/coverage terdefinisi di Makefile (enforcement 85% mulai M6)

## Catatan sesi / keputusan sprint ini

- (diisi oleh agent setiap sesi)
