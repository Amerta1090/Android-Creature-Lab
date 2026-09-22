# Microtask Backlog — Master Checklist

> Dibuat otomatis dari `docs/PRD.md` §O · Total task terjadwal: **106** · Update: centang DI SINI dan di sprint file saat task selesai.

## Sprint 01 — M0: Repository / Architecture
- [x] R-001 — Initialize monorepo skeleton
- [x] R-002 — Python package skeleton + toolchain
- [x] R-003 — Config system
- [x] R-004 — Structured logging
- [x] R-005 — Clock abstraction
- [x] R-006 — Seeded RNG utility
- [x] R-007 — Error taxonomy
- [ ] R-008 — Docs skeleton + ADRs
- [ ] R-009 — Dev runner + lint gates

## Sprint 02 — M1: Android Connection Layer
- [ ] A-001 — AdbClient (wire wrapper)
- [ ] A-002 — Device discovery + serial targeting
- [ ] A-003 — Connection state machine + supervision
- [ ] A-004 — Device info (getprop) reader
- [ ] A-005 — Fixture transport (recorded adb)
- [ ] A-006 — Adapter tests (incl. malformed/timeout/version variants)
- [ ] A-007 — Failure-mode tests (adb absent/offline/killed)

## Sprint 03 — M2: Device Perception
- [ ] P-001 — Observation schema
- [ ] P-002 — Battery observer (`dumpsys battery`)
- [ ] P-003 — Screen/wakefulness observer
- [ ] P-004 — Foreground app observer
- [ ] P-005 — CPU / load observer (`dumpsys cpuinfo`)
- [ ] P-006 — Memory observer (`dumpsys meminfo`)
- [ ] P-007 — Storage observer (`df /data`)
- [ ] P-008 — Network observer (`dumpsys connectivity`)
- [ ] P-009 — Uptime/display/orientation observer
- [ ] P-010 — Polling scheduler (adaptive)
- [ ] P-011 — Edge detection → derived events
- [ ] P-012 — Observation store
- [ ] P-013 — Perception end-to-end tests

## Sprint 04 — M3: Creature State
- [ ] C-001 — CreatureState schema
- [ ] C-002 — State persistence
- [ ] C-003 — Activity state machine
- [ ] C-004 — Stat dynamics registry
- [ ] C-005 — State/stat unit tests consolidated

## Sprint 05 — M4: Decision Engine
- [ ] D-001 — Context builder
- [ ] D-002 — Need evaluation
- [ ] D-003 — Candidate action model + registry
- [ ] D-004 — Utility scoring
- [ ] D-005 — Deterministic selector
- [ ] D-006 — Decision record + logging
- [ ] D-007 — Decision log store
- [ ] D-008 — Determinism golden tests

## Sprint 06 — M5: Creature Actions
- [ ] X-001 — Action interface + registry + allowlist
- [ ] X-002 — Action backends (real vs sim)
- [ ] X-003 — Notify action
- [ ] X-004 — Vibrate action
- [ ] X-005 — Brightness action
- [ ] X-006 — Volume action
- [ ] X-007 — Launch-app action
- [ ] X-008 — Battery-saver toggle (EXPERIMENTAL)
- [ ] X-009 — Safety gate enforcement + failure signals
- [ ] X-010 — Cooldowns / rate limits
- [ ] X-011 — Action test suite (fixtures + failure modes)

## Sprint 07 — M6: Creature Memory
- [ ] M-001 — Event store schema
- [ ] M-002 — Short-term ring memory
- [ ] M-003 — Importance scoring
- [ ] M-004 — Long-term pattern extraction
- [ ] M-005 — Consolidation job
- [ ] M-006 — Memory query API
- [ ] M-007 — Memory tests + determinism

## Sprint 08 — M7: Simulation
- [ ] S-001 — Fake device environment
- [ ] S-002 — Scenario DSL
- [ ] S-003 — Headless sim runner
- [ ] S-004 — Preset scenarios
- [ ] S-005 — Simulation test harness + determinism
- [ ] S-006 — Step/replay debug CLI

## Sprint 09 — M8: Pokédex Inventory
- [ ] K-001 — Pokedex schema + store
- [ ] K-002 — Identity collector
- [ ] K-003 — Package inventory collector
- [ ] K-004 — Package detail collector
- [ ] K-005 — Permission collector
- [ ] K-006 — Components collector
- [ ] K-007 — Parsers & malformed-output tests (batch)
- [ ] K-008 — CLI wiring (scan/apps/permissions/components)

## Sprint 10 — M9: Pokédex Runtime
- [ ] K2-001 — Process collector
- [ ] K2-002 — CPU/RAM runtime totals
- [ ] K2-003 — Foreground runtime monitor
- [ ] K2-004 — Network/battery/temp runtime
- [ ] K2-005 — Runtime store + CLI
- [ ] K2-006 — Runtime tests

## Sprint 11 — M10: Snapshot / Diff
- [ ] DP-001 — Snapshot model + capture
- [ ] DP-002 — Diff engine
- [ ] DP-003 — ChangeSet model
- [ ] DP-004 — Snapshot/diff CLI
- [ ] DP-005 — Diff golden tests

## Sprint 12 — M11: Historical Device Model
- [ ] H-001 — Snapshot history store
- [ ] H-002 — Change-event derivation
- [ ] H-003 — Device fingerprint
- [ ] H-004 — Trends / mini-reports
- [ ] H-005 — History/fingerprint CLI

## Sprint 13 — M12: Creature + Pokédex Integration
- [ ] I-001 — EnvironmentModel bridge
- [ ] I-002 — Perception gateway
- [ ] I-003 — Creature runtime on real device
- [ ] I-004 — Action routing via environment + safety
- [ ] I-005 — End-to-end observability
- [ ] I-006 — E2E integration tests

## Sprint 14 — M13: UI / Visualization
- [ ] U-001 — CLI rendering
- [ ] U-002 — Decision explain view
- [ ] U-003 — History export (HTML/text)
- [ ] U-004 — Watch mode

## Sprint 15 — M14: Hardening / Documentation
- [ ] N-001 — Failure-injection suite
- [ ] N-002 — Soak test (24 h)
- [ ] N-003 — Docs: troubleshooting + dev guide
- [ ] N-004 — Performance budgets + benchmarks
- [ ] N-005 — Release/versioning/changelog
- [ ] N-006 — Security review pass

## Deferred (tidak terjadwal, butuh persetujuan user)
- [ ] X-SND — Sound action (media play)
- [ ] K2-007 — logcat event stream (opsional push channel)
- [ ] U-005 — rich/matplotlib dashboards (butuh ticket + justifikasi, PRD §0.10)
- [ ] A-008 — WiFi-adb pairing assistant
- [ ] LLM-001 — Local analysis layer (konsultatif pada data terekam saja; TIDAK dijadwalkan)