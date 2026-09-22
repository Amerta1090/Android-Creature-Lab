# Sprint 03 — M2: Device Perception

- Status: `NOT STARTED`
- Objective: Observation schema, observer (battery/screen/fg/cpu/mem/storage/net/uptime), scheduler adaptif, edge detection, observation store, E2E test.
- Entry criteria: M1 selesai.
- Spec task: `docs/PRD.md` §O (M2) · Checklist master: `docs/backlog.md`

## Tasks

- [ ] **P-001 — Observation schema**
- [ ] **P-002 — Battery observer (`dumpsys battery`)**
- [ ] **P-003 — Screen/wakefulness observer**
- [ ] **P-004 — Foreground app observer**
- [ ] **P-005 — CPU / load observer (`dumpsys cpuinfo`)**
- [ ] **P-006 — Memory observer (`dumpsys meminfo`)**
- [ ] **P-007 — Storage observer (`df /data`)**
- [ ] **P-008 — Network observer (`dumpsys connectivity`)**
- [ ] **P-009 — Uptime/display/orientation observer**
- [ ] **P-010 — Polling scheduler (adaptive)**
- [ ] **P-011 — Edge detection → derived events**
- [ ] **P-012 — Observation store**
- [ ] **P-013 — Perception end-to-end tests**

## Exit criteria (SEMUA harus terpenuhi sebelum sprint ditandai COMPLETE)

- [ ] creature observe menampilkan Observation lengkap di mode sim + fixture
- [ ] Semua observer punya parser test + UNKNOWN fallback
- [ ] Edge events (BATTERY_LOW, SCREEN_ON, dll) teruji

## Catatan sesi / keputusan sprint ini

- (diisi oleh agent setiap sesi)
