# Sprint 02 — M1: Android Connection Layer

- Status: `NOT STARTED`
- Objective: AdbClient, discovery, connection state machine, getprop, fixture transport, fault tests.
- Entry criteria: M0 selesai.
- Spec task: `docs/PRD.md` §O (M1) · Checklist master: `docs/backlog.md`

## Tasks

- [ ] **A-001 — AdbClient (wire wrapper)**
- [ ] **A-002 — Device discovery + serial targeting**
- [ ] **A-003 — Connection state machine + supervision**
- [ ] **A-004 — Device info (getprop) reader**
- [ ] **A-005 — Fixture transport (recorded adb)**
- [ ] **A-006 — Adapter tests (incl. malformed/timeout/version variants)**
- [ ] **A-007 — Failure-mode tests (adb absent/offline/killed)**

## Exit criteria (SEMUA harus terpenuhi sebelum sprint ditandai COMPLETE)

- [ ] Test adapter hijau offline (fixture transport, tanpa adb)
- [ ] State machine menangani connect/disconnect (test)
- [ ] Discovery mendukung multi-device by serial

## Catatan sesi / keputusan sprint ini

- (diisi oleh agent setiap sesi)
