# Status Proyek — Android Creature → Pokédex

> **File ini adalah SINGLE SOURCE OF TRUTH untuk kemajuan proyek.**
> Diupdate oleh agent SETIAP kali microtask selesai / akhir sesi. Jangan mengandalkan ingatan — baca file ini.
> Protokol kerja: `prompt.md` · Plan: `docs/PRD.md` · Sprint: `docs/sprints/`

---

## Progress Snapshot (per 2026-09-22)

- Repo: `/home/amerta/Android Creature Lab`
- Git: **ter-initialize, branch `main`, remote `origin` → https://github.com/Amerta1090/Android-Creature-Lab.git** (first commit `62270f0`, sudah di-push 2026-09-22)
- Catatan: `.gitignore` sudah dibuat saat setup repo; task `R-001` tinggal verifikasi/melengkapi + README + LICENSE + git init tidak perlu diulang.
- Sprint aktif: **Sprint 1 — M0: Repository / Architecture**
- Status sprint aktif: `IN PROGRESS` (3/9) — R-001, R-002, R-003 done
- Task selesai: **3 / 106**
- Task berjalan: **R-004 — Structured logging**
- Blocked: — (tidak ada)
- Device Android: **terhubung** (per 2026-09-22) — vivo V2157, Android 14 (API 34), serial `34454119440004U` (USB)

## Environment Baseline (diverifikasi 2026-09-22)

| Item | Nilai |
|------|-------|
| adb | 1.0.41 (android-tools 37.0.0), `/usr/bin/adb` |
| python3 | 3.14.7 |
| git | 2.55.0 |
| sqlite3 | 3.53.4 |
| pytest | belum terpasang (dep dev; dipasang via `scripts/setup.sh`, task R-002) |
| device android | vivo V2157 / Android 14 / `34454119440004U` (`adb devices -l` kosong sebelumnya, terhubung 2026-09-22) |

> Catatan: jika environment berubah di sesi berikutnya, agent update tabel ini.

## Ringkasan Sprint (detail & checklist: `docs/sprints/`)

| Sprint | Milestone | Status | Tasks done |
|--------|-----------|--------|-----------|
| Sprint | Milestone | Status | Tasks done |
|--------|-----------|--------|-----------|
| 01 | M0 — Repository / Architecture | `IN PROGRESS` | 2 / 9 |
| 02 | M1 — Android Connection Layer | `NOT STARTED` | 0 / 7 |
| 03 | M2 — Device Perception | `NOT STARTED` | 0 / 13 |
| 04 | M3 — Creature State | `NOT STARTED` | 0 / 5 |
| 05 | M4 — Decision Engine | `NOT STARTED` | 0 / 8 |
| 06 | M5 — Creature Actions | `NOT STARTED` | 0 / 11 |
| 07 | M6 — Creature Memory | `NOT STARTED` | 0 / 7 |
| 08 | M7 — Simulation | `NOT STARTED` | 0 / 6 |
| 09 | M8 — Pokédex Inventory | `NOT STARTED` | 0 / 8 |
| 10 | M9 — Pokédex Runtime | `NOT STARTED` | 0 / 6 |
| 11 | M10 — Snapshot / Diff | `NOT STARTED` | 0 / 5 |
| 12 | M11 — Historical Device Model | `NOT STARTED` | 0 / 5 |
| 13 | M12 — Creature + Pokédex Integration | `NOT STARTED` | 0 / 6 |
| 14 | M13 — UI / Visualization | `NOT STARTED` | 0 / 4 |
| 15 | M14 — Hardening / Documentation | `NOT STARTED` | 0 / 6 |

## Open Questions

| # | Pertanyaan | Status |
|---|-----------|--------|
| 1 | Device test target (model + Android version)? | `RESOLVED` — vivo V2157, Android 14 (API 34), serial `34454119440004U` (per 2026-09-22). Tidak memblokir M0–M7. |
| 2 | USB atau adb-over-WiFi? | `OPEN` — default USB; tidak memblokir. |
| 3 | Device selalu terhubung atau sesekali? | `OPEN` — diasumsikan sesekali (dev sim-first). |
| 4 | Aksi audible/visible boleh selama dev? | `OPEN` — default SAFE on, CONTROL di-gate config. |
| 5 | Local LLM diinginkan (untuk "explain" data terekam)? | `OPEN` — default tidak; dibahas pasca-M14. |
| 6 | Device boleh tidur normal? | `OPEN` — default boleh; kreatur bereaksi, tidak mencegah tidur. |
| 7 | Locale/timezone device? | `OPEN` — diasumsikan pakai `persist.sys.timezone`. |
| 8 | Multi-device concurrent untuk v1? | `OPEN` — v1 = satu device aktif; arsitektur sudah serial-keyed. |

## ADR Index

- ADR-001..ADR-008: **belum dibuat** → dibuat di task `R-008` (daftar topik di PRD §0 / `docs/PRD.md`).

## Aturan Pemeliharaan (untuk agent)

1. Setelah tiap task selesai: centang di sprint file + `docs/backlog.md`, update baris *Progress Snapshot* di file ini, append `docs/session-log.md`, commit.
2. Akhir sprint: verifikasi exit criteria sprint → update status sprint jadi `COMPLETE` → buka sprint berikutnya di README sprints.
3. Perubahan arsitektur → ADR baru di `docs/adr/` + konfirmasi user (PRD §21.6).
4. Jika task "berjalan" tercatat (ada ID di *Task berjalan*), sesi berikutnya LANJUTKAN task itu — jangan mulai task lain.
5. Jangan mengubah struktur task di sprint file; kalau backlog berubah, edit `docs/PRD.md` §O lalu regenerate (lihat catatan regenerasi di `docs/sprints/README.md`).