# Session Log — Android Creature → Pokédex

> Log append-only. Satu entri per sesi kerja (atau per akhir sesi jika sesi panjang).
> Format entri baru disalin dari template di bawah. Agent WAJIB mengisi saat selesai per task / sesi.

---

## Template Entri

```
## YYYY-MM-DD — Sesi N — <judul singkat>

- **State awal:** sprint <NN>, <task berjalan atau "tidak ada">
- **Kerja:** <daftar task yang dikerjakan, ID — title>
- **Tests:** <hasil test / lint>
- **Issues ditemukan:** <atau "tidak ada">
- **Perubahan state:** <task selesai x→y, sprint baru dibuka, dsb>
- **Keputusan/ADR:** <bila ada>
- **Commits:** <daftar hash/subjek>
- **Next:** <task berikutnya>
```

---

## 2026-09-22 — Sesi 2 — HP terhubung + verifikasi env + perbaikan index sprint stale

- **State awal:** Sprint 1 (M0) IN PROGRESS 2/9 (R-001, R-002 done), Task berjalan: tidak ada.
- **Kerja:** Sesuai `prompt.md`: verifikasi environment (adb/python). Device Android **terhubung** — vivo V2157, Android 14 (API 34), serial `34454119440004U` (USB, transport_id 3). Open Question #1 (device test target) → RESOLVED, dicatat di `docs/status.md`. Konflik dokumen: index `docs/sprints/README.md` menampilkan semua sprint COMPLETE padahal hanya R-001/R-002 selesai → atas persetujuan user, tabel index diperbaiki (Sprint 1 `IN PROGRESS (2/9)`, Sprint 2–15 `NOT STARTED`).
- **Tests:** tidak ada kode proyek berubah.
- **Issues ditemukan:** `sprints/README.md` index stale (sudah diperbaiki); device target sebelumnya kosong → terisi.
- **Perubahan state:** device Android terhubung & tercatat; OQ#1 RESOLVED; README index sprint konsisten dengan status.md/backlog. Task selesai tetap 2/106.
- **Keputusan/ADR:** device baseline fixture = vivo V2157 / Android 14 (untuk M1/M8+ tuning, dan I-003/Sprint 13 nanti).
- **Commits:** <dibuat di akhir sesi ini>
- **Next:** lanjut Sprint 1 (M0) — verifikasi R-001 (.gitignore sudah ada), R-003 Config system, dst.

---

## 2026-09-22 — Sesi 1 — Git setup + push pertama ke GitHub

- **State awal:** repo belum di-init; hanya file planning + sistem iteratif (sesi 0).
- **Kerja:** sesuai permintaan user `git remote add origin …` + `branch -M main` + `push -u origin main`; ditambah prasyarat: `git init`, `.gitignore`, commit pertama.
- **Verifikasi:** git identity (Amerta1090 / abdulmajidr708@gmail.com), `gh` terautentikasi (https), remote GitHub `Amerta1090/Android-Creature-Lab` ada & kosong (`ls-remote` exit 0).
- **Tests:** tidak ada kode proyek.
- **Issues ditemukan:** tidak ada.
- **Perubahan state:** repo `main` = commit `62270f0` (24 files, 2756 insertions), ter-push ke origin. `.gitignore` sudah dibuat (R-001 tinggal verifikasi). Sprint 1 tetap `NOT STARTED`, 0/106 task.
- **Commits:** `62270f0` Initial commit: planning package (PRD) + iterative development system.
- **Next:** Sprint 1 (M0) dimulai setelah persetujuan user — R-001 (README/LICENSE/dirs + verifikasi .gitignore), R-002 dst.

---

## 2026-09-22 — Sesi 0 — Setup sistem pengembangan iteratif

- **State awal:** proyek baru, hanya `docs/PRD.md` (perencanaan selesai).
- **Kerja:** membuat sistem iteratif:
  - `prompt.md` — protokol kerja agent (entry point, resume algorithm, DoD, pelaporan, anti-pola).
  - `AGENTS.md` — pointer ringkas untuk agent.
  - `docs/status.md` — single source of truth kemajuan + environment baseline.
  - `docs/session-log.md` — log sesi (file ini).
  - `docs/backlog.md` + `docs/sprints/*.md` (15 sprint) + `docs/sprints/README.md` — di-generate dari PRD §O (106 task) via `scripts/gen_sprints.py`.
  - PRD: angka backlog dikoreksi (80/94 → 106, sesuai hasil generate).
- **Tests:** tidak ada kode proyek; generator sprint diuji sekali jalan (output 15 sprint, 106 task).
- **Issues ditemukan:** PRD sebelumnya menulis 94 task padahal 106 — sudah dikoreksi.
- **Perubahan state:** Sprint 1 siap dimulai (`NOT STARTED`), 0/106 task.
- **Keputusan/ADR:** tidak ada perubahan arsitektur (murni tooling proses).
- **Commits:** belum ada (git init dilakukan di R-001).
- **Next:** Sprint 1 (M0) — R-001 (git init + skeleleton repo), bila user menyetujui untuk mulai.
## 2026-09-22 — Sesi 1 (lanjutan) — R-001 finalization

- **State awal:** Sprint 1 (M0) `IN PROGRESS`; R-001 sudah commit kode (`04474eb` — README, LICENSE, dirs src/tests/data). Note: `docs/sprints/README.md` index table keliru menampilkan SEMUA sprint `COMPLETE` — ini bertentangan dgn status.md/sprint file/git log; akan di-regenerate/benahi di R-008.
- **Kerja:** R-001 — verifikasi DoD (dirs exist, data/ ignored, README two-phase, LICENSE MIT) + centang backlog & sprint file + snapshot status → `IN PROGRESS 1/9 · 1/106`.
- **Tests:** make lint belum ada (R-009); tidak ada kode proyek selain skeleton → no-op.
- **Issues ditemukan:** (1) `docs/sprints/README.md` index stale (semua COMPLETE) — dibuat otomatis, jangan diedit manual; fix via R-008. (2) README worktree sudah benar, tidak perlu regenerasi.
- **Perubahan state:** task selesai 0 → 1 (R-001 done).
- **Commits:** `04474eb` R-001 — Initialize monorepo skeleton.
- **Next:** R-002 — Python package skeleton + toolchain.

## 2026-09-22 — Sprint 1 (R-002) — Python package skeleton + toolchain

- **State awal:** Sprint 01 M0 `IN PROGRESS` 1/9 (R-001 done `da40fb8`). Backlog R-002 unchecked.
- **Kerja (test-first, R-002 DoD):** pyproject.toml (setuptools>=75 pin, stdlib-only runtime, `[project.scripts] creature/pokedex`, pytest+coverage config), `src/android_creature/__init__.py` (__version__="0.1.0" single-source), `cli/main.py` (`creature`/`pokedex` entry funcs — `--version` exit 0), `cli/__init__.py` (package marker), tests/conftest.py (frozen clock + seeded LCG fixtures — no wall-clock; deterministic), tests/smoke/test_version.py + tests/unit/test_package.py (PEP440 sortable version), tests/unit/__init__.py. `.venv` + `pip install -e .[dev]` (pytest 9.1.1).
- **Verifikasi (gate):** `pytest` **4 passed**; `creature --version` & `pokedex --version` exit 0 → 0.1.0; `python -m compileall` clean; **grep anti-pattern clean** (no datetime.now/time.time/random in src) — PRD wall-clock gate satisfied early.
- **Tests:** 4 passed (2 smoke/unit version), 0 failed.
- **Issues ditemukan:** (1) test basename collision `test_version` di tests/smoke vs tests/unit → pytest import-mismatch; fix: rename unit file ke `test_package.py`. (2) `docs/sprints/README.md` index masih menyiratkan semua sprint COMPLETE — generated, bona fide di R-008 docs task. (3) .gitignore sudah memuat `data/` — sinkron dgn R-002 DoD.
- **Perubahan state:** task selesai 1 → 2 · Sprint 01 `IN PROGRESS` (2/9) · backlog + sprint-01 check R-002.
- **Keputusan/ADR:** — (tidak ada; toolchain murni eksekusi DoD, tidak mengubah arsitektur).
- **Commits:** (ditambahkan saat commit keluar) R-002 — Python package skeleton + toolchain.
- **Next:** R-003 — Config system.

## 2026-09-22 — Sesi 517 (R-002) — Struktur package Python + toolchain (R-002 done)

- **State awal:** Sprint 1 M0 `IN PROGRESS` (1/9); R-002 unchecked; ct `android_creature` ada di src.
- **Kerja (test-first, R-002 DoD):** `pyproject.toml` (setuptools>=75, `[project.scripts] creature/pokedex`, PEP 440 dynamic version `0.1.0`, pytest+coverage config), `src/android_creature/__init__.py` (__version__="0.1.0", single source), `src/android_creature/cli/__init__.py` + `cli/main.py` (`creature`/`pokedex` console funcs → `_run` prints version/usage, `--version` exit 0), `.venv` + `pip install -e .[dev]` (pytest 9.1.1), `tests/conftest.py` (frozen clock + seeded LCG fixtures — no wall clock, stdlib-only), `tests/smoke/test_version.py` (both `--version` exit 0) + `tests/unit/test_package.py` (PEP440-sortable version, single-source symbol).
- **Verifikasi/gate:** pyt `android_creature` importable; `pytest` **4 passed**; `creature --version` & `pokedex --version` exit 0 → `0.1.0`; `python -m compileall` clean; **grep gate clean** (no `datetime.now/time.time/wall-clock` in src — R-009 anti-pattern already satisfiable).
- **Issues ditemukan:** (1) colliding basename: dua `tests/*/test_version.py` (smoke + unit) → pytest `import file mismatch`; fixed: unit renamed `test_package.py` (unique basename across suite; pytest import habits documented). (2) `docs/sprints/README.md` index stale (all sprints COMPLETE) — generated file, dibenahi di R-008 (regenerate from PRD §O), JANGAN hand-edit.
- **Perubahan state:** task selesai 1 → 2 (R-002 done); Sprint 1 `IN PROGRESS` (2/9); sampel status sprint di `status.md` updated.
- **Keputusan/ADR:** tidak ada ADR baru (toolchain murni; pyproject + DoD sudah menetapkan arah — konform PRD §R-002).
- **Next:** R-003 — Config system.

---

## 2026-09-22 — Sesi 2 — R-003 Config system + verifikasi device vivo V2157

- **State awal:** Sprint 1 (M0) IN PROGRESS 2/9 · task berjalan R-003.
- **Kerja:** R-003 — Config system: `config.py` (layered defaults < `data/config.json` < env `ACL_*` < CLI; deep-merge non-mutating; schema `.json` deterministic; `load_config_with_warnings`), CLI wiring `config show/validate/set` (exit 5 untuk config invalid, konsisten PRD R-003 §doD & R-007), 21 unit tests. Verifikasi device Android nyata: **vivo V2157, Android 14 (API 34), serial `34454119440004U`** — dicatat di `docs/status.md` (Open Question #1 RESOLVED).
- **Tests:** 25 passed (unit+smoke). Gate wall-clock `grep` pada `src/` bersih.
- **Issues ditemukan:** docs/sprints/README.md index stale (semua sprint terlabel COMPLETE padahal baru 2 task selesai) → diperbaiki atas konfirmasi user; tabel index kini IN PROGRESS (3/9) + NOT STARTED. `pyproject.toml` belum punya entry-point `config` di backlog (hanya wired di CLI) — didokumentasikan di session-log.
- **Perubahan state:** task selesai 2 → 3; `docs/status.md` + `docs/backlog.md` + `docs/sprints/sprint-01-m0.md` + README index diupdate; device target terisi.
- **Commits:** `<commit R-003>` (config system) — belum di-push (push menyusul setelah checkout preset).
- **Next:** R-004 — Structured logging (`logging.py`).

---

## 2026-09-22 — Sesi 2 (lanjutan) — R-004 Structured logging (dikoreksi + diimplementasi)

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 3/9 · task berjalan R-004.
- **Konflik ditemukan:** commit `52bf4e9` (docs R-003) keliru mencentang **R-004** di `docs/backlog.md` dan `sprint-01-m0.md` padahal belum ada implementasi/tests/commit sama sekali (`logging.py` tidak ada, `git log` tanpa "R-004"). `docs/status.md` (source of truth) sudah benar: 3/106, task berjalan R-004. Sesuai protokol §5 (konflik status/docs → tanyakan), dikonfirmasi ke user → disetujui: **koreksi checkbox + implementasi R-004 dari nol**.
- **Kerja (test-first, R-004 DoD):**
  - Checkbox R-004 direvert ke `[ ]` (backlog + sprint file) sebagai penanda aman, lalu diisi ulang setelah DoD terpenuhi.
  - `src/android_creature/logging.py` — thin wrapper stdlib: `get_logger(name)` (single import surface; komponen = nama dotted `android_creature.<name>`), `configure_logging(level=None, format_spec=None)` idempotent (handler diganti, tidak menumpuk → "never duplicates frames"), level dari config `logging.level` (default `info`), format `HH:MM:SS.mmm LEVEL component message` (`%(asctime)s.%(msecs)03d %(levelname)s %(name)s %(message)s`, datefmt `%H:%M:%S`), StreamHandler → **stderr saja**; config invalid tidak menggagalkan setup (config CLI tetap exit 5); tanpa impor `time`/`datetime` (timestamp dirender stdlib di boundary — determinisme PRD NFR-2 aman).
  - `cli/main.py` — wiring `-v`/`--verbose` (acceptance: `-v` tampilkan debug, default sembunyikan); usage/docstring diperbarui; output mesin tetap di stdout.
  - `tests/unit/test_logging.py` (new) — 13 tests.
- **Tests:** **38 passed** (0 failed) · `python -m compileall` clean · grep gate wall-clock/random pada `src/` CLEAN · `creature/pokedex --version` exit 0 · `creature config validate` exit 0.
- **Acceptance end-to-end:** default → debug disembunyikan, `INFO android_creature.perception INFO-VISIBLE` tampil; `-v` → `DEBUG android_creature.perception DEBUG-VISIBLE-WITH-V` tampil. Machine output (`config OK`) tetap stdout, log di stderr.
- **Issues ditemukan:** (1) checkbox R-004 salah centang (root cause di atas; sudah dikoreksi via sesi ini); (2) SyntaxWarning `\d` di docstring test → dirapikan.
- **Perubahan state:** task selesai 3 → 4 (R-004 done) · Sprint 01 `IN PROGRESS` (4/9) · `status.md`/`backlog.md`/`sprint-01-m0.md`/`README` index diupdate · Task berjalan dikosongkan (next: R-005).
- **Keputusan/ADR:** — (tidak ada perubahan arsitektur; config `logging.format` diperlakukan sebagai *template* bentuk baris, `%`-format kustom dihormati sebagai escape hatch — didokumentasikan di docstring logging.py).

---

## 2026-09-22 — Sesi 3 — R-005 Clock abstraction

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 4/9 · task berjalan tidak ada (next R-005).
- **Kerja (test-first, R-005 DoD):**
  - `src/android_creature/clock.py` — `Clock` protocol (`now() -> float`, `iso() -> str`, `tick_id -> int`); `SystemClock` adapter (now = `time.monotonic()`, iso = UTC-Z via `time.gmtime()`, tick_id = int monotonic) sebagai **global default** `clock`; `SimClock` (origin default `2026-01-01T00:00:00`, `advance(sec>=0)` → elapsed + tick_id +1 per call termasuk step 0, now = epoch sim, iso = `YYYY-MM-DDTHH:MM:SS.mmmZ` deterministik); modul default diganti di tests/sim.
  - **Hygiene determinisme:** `clock.py` menghindari token banned API sepenuhnya (tanpa `datetime.now`/`time.time` — wall time via `monotonic`/`gmtime`), sehingga grep gate tetap CLEAN tanpa pengecualian file; dijamin oleh test `test_clock_adapter_avoids_banned_api_tokens` + `test_only_clock_adapter_imports_time_datetime` (preview lint R-009).
  - `tests/conftest.py` — `_FrozenClock` stand-in diganti `SimClock` sungguhan sekaligus dipasang sebagai `android_creature.clock.clock` via monkeypatch (sesuai PRD "replaced in tests/sim"); `seeded_rng` tetap (digantikan R-006).
  - `tests/unit/test_clock.py` (new) — 14 tests.
- **Tests:** **53 passed** (0 failed) · `python -m compileall` clean · grep gate banned-API pada `src/` CLEAN · `creature/pokedex --version` exit 0 · `creature config validate` exit 0.
- **Issues ditemukan:** (1) test token-banned menangkap docstring `clock.py` yang menyebut `datetime.now`/`time.time` secara literal → docstring di-reword agar source bebas token (test bekerja sebagaimana dimaksud). (2) step `advance(0.0)` memutus asumsi kemonotonan ketat di test → dipisah: `advance(0)` menaikkan tick tanpa menggerakkan waktu (idle tick), didokumentasikan.
- **Perubahan state:** task selesai 4 → 5 (R-005 done) · Sprint 01 `IN PROGRESS` (5/9) · `status.md`/`backlog.md`/`sprint-01-m0.md`/`README` index diupdate · Task berjalan dikosongkan (next: R-006).
- **Keputusan/ADR:** — (tidak ada; konsisten PRD R-005 — SystemClock adapter sebagai default, SimClock untuk sim/test).

---

## 2026-09-22 — Sesi 3 (lanjutan) — R-006 Seeded RNG utility

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 5/9 · task berjalan tidak ada (next R-006).
- **Kerja (test-first, R-006 DoD):**
  - `src/android_creature/rng.py` — `SeededRng(seed, tick=0)`: `rand_float(a=0.0, b=1.0)` (interval apa pun urutannya), `choice(weighted)` (pasangan `(value, weight)`, weight ≥ 0, total > 0, `target <= cumulative`), `set_tick(tick)` → **per-tick stability** (seed+tick sama ⇒ stream identik; tick baru ⇒ stream baru deterministik). Seed dimix numerik dengan tick (`(seed << 32) ^ (tick & 0xFFFFFFFF)`) — tanpa argumen string seed (bisa jadi tidak deterministik antar proses karena hash randomization).
  - **Desain determinisme kunci:** hanya `from random import Random` + panggil `Random.uniform(...)` — source `src/` **bebas token `random.`** sehingga grep gate `\brandom\.` tetap CLEAN tanpa pengecualian (DoD "no module-level random leakage" terpenuhi secara harfiah & semangat).
  - `tests/conftest.py` — placeholder LCG `seeded_rng` diganti `SeededRng(0xC0FFEE)` sungguhan (source of truth R-006).
  - `tests/unit/test_rng.py` (new) — 16 tests (reproducibility, bounds, weighted edge cases, per-tick stability, hygiene import + token).
- **Tests:** **71 passed** (0 failed) · compileall clean · grep gate CLEAN · verifikasi determinisme **lintas proses** (dua proses `python -c` terpisah → stream identik).
- **Issues ditemukan:** docstring `rng.py` memuat literal ``random.``-API → tertangkap hygiene test → di-reword (test bekerja sebagaimana dimaksud, sama polanya dengan R-005).
- **Perubahan state:** task selesai 5 → 6 (R-006 done) · Sprint 01 `IN PROGRESS` (6/9) · `status.md`/`backlog.md`/`sprint-01-m0.md`/`README` index diupdate · Task berjalan dikosongkan (next: R-007).
- **Keputusan/ADR:** — (tidak ada; stdlib `Random` int-seeded dipilih karena deterministik lintas proses; mixing seed+tick numerik -> tidak ada hash randomization).

---

## 2026-09-22 — Sesi 3 (lanjutan) — R-007 Error taxonomy

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 6/9 · task berjalan tidak ada (next R-007).
- **Kerja (test-first, R-007 DoD):**
  - `src/android_creature/errors.py` — `LabError(Exception)` base dengan atribut kelas `exit_code`; `ConfigError` (5), `NoDeviceError` (3), `SafetyBlockedError` (4), `AdbError` base + kind typed: `AdbMissingBinaryError`/`AdbTransportError`/`AdbTimeoutError`/`AdbDeviceError` (semua → 1; dipakai A-001 untuk retry/install), `ParseError(message, details)`; `to_exit_code(exc)` resolusi via MRO (`getattr(type(exc), "exit_code", 1)`) — mapping subclass otomatis, default 1 untuk yang lupa di-map (failure mode R-007).
  - **Konsolidasi:** `config.py` — class `ConfigError` lokal dihapus, diganti alias `config.ConfigError = errors.ConfigError`; `CONFIG_ERROR_EXIT = errors.ConfigError.exit_code` (satu sumber). Tidak ada test lama yang rusak (25 test config tetap hijau).
  - `cli/main.py` — top-level handler `except errors.LabError` → one-line `error: <msg>` di stderr + `to_exit_code` (acceptance R-007); path config lama (exit 5, "config error:") tidak berubah.
  - `tests/unit/test_errors.py` (new) — 12 tests (mapping, inheritance, chaining `__cause__`, ParseError details, konsolidasi config, CLI handler exit 3/1/5).
- **Tests:** **84 passed** (0 failed) · compileall clean · grep gate CLEAN · entry smoke ok · mapping terverifikasi `{ConfigError:5, NoDeviceError:3, SafetyBlockedError:4, AdbTimeoutError:1, LabError:1}`.
- **Issues ditemukan:** (1) sisa `_boom` yang mereferensikan class tak ada di test CLI → dibersihkan. (2) tidak ada (config alias tidak merusak test lama).
- **Perubahan state:** task selesai 6 → 7 (R-007 done) · Sprint 01 `IN PROGRESS` (7/9) · `status.md`/`backlog.md`/`sprint-01-m0.md`/`README` index diupdate · Task berjalan dikosongkan (next: R-008 — Docs skeleton + ADRs).
- **Keputusan/ADR:** — (tidak ada; exit-code sebagai atribut kelas dipilih supaya `to_exit_code` satu-liner via MRO, default 1 sebagai safety net — sesuai failure mode R-007).

---

## 2026-09-22 — Sesi 3 (lanjutan) — R-008 Docs skeleton + ADRs

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 7/9 · task berjalan tidak ada (next R-008).
- **Kerja (R-008 DoD):**
  - `docs/adr/README.md` — index 8 ADR + **template ADR** untuk ADR berikutnya (Context/Decision/Consequences, status Proposed→Accepted, aturan update; sesuai DoD "template documented in README").
  - `docs/adr/ADR-001..008.md` — masing-masing satu halaman, decisions mencerminkan PRD §0: 001 Python/stdlib (0.1, 0.10) · 002 host-side runtime (0.2) · 003 adb CLI wrapper (0.3) · 004 storage SQLite+JSON+JSONL (0.6) · 005 determinism policy (0.7) · 006 no-LLM-in-loop (0.8) · 007 poll+edge events (0.5) · 008 no-root baseline (0.4).
  - `status.md` — section ADR Index diisi (list ADR + lokasi). README utama ditambah pointer ke `docs/adr/README.md`.
  - `docs/PRD.md` sudah ter-commit sejak initial commit — tidak ada perubahan konten (R-008 scope "commit PRD" terpenuhi).
- **Tests:** tidak ada (spec R-008: Tests: none). Gate: `pytest` tetap **84 passed**; ukuran file dicek (tiap ADR 1 halaman).
- **Issues ditemukan:** tidak ada. Generator sprints TIDAK dijalankan (di luar scope; index sprint sudah benar pasca-Sesi 2).
- **Perubahan state:** task selesai 7 → 8 (R-008 done) · Sprint 01 `IN PROGRESS` (8/9) · `status.md`/`backlog.md`/`sprint-01-m0.md`/`README` index diupdate · Task berjalan dikosongkan (next: R-009).
- **Keputusan/ADR:** ADR-001..008 dibuat sesuai default PRD §0 (tidak ada keputusan baru; catat sebagai baseline decisions).

---

## 2026-09-22 — Sesi 4 — R-009 Dev runner + lint gates + penutupan Sprint 1 (M0)

- **State awal:** Sprint 1 (M0) `IN PROGRESS` 8/9 · task berjalan tidak ada (next R-009).
- **Kerja (R-009 DoD):**
  - `Makefile` — target `setup` (venv+install via `scripts/setup.sh`), `test` (`pytest tests -m "not hw"` — unit/sim/adapter/regression offline), `test-hw` (`-m hw`, device), `lint` (compileall + src hygiene), `record-fixture` (stub, wiring di A-005), `clean`.
  - `scripts/setup.sh` — bootstrap `.venv` + `pip install -e .[dev]`, idempotent, offline-friendly.
  - `scripts/check_src_hygiene.py` — lint AST/teks: token banned (`datetime.now`, `time.time`, `random.`) + import stdlib-only (`sys.stdlib_module_names`) & pengelompokan stdlib-dulu.
  - `tests/README.md` — struktur tier (unit/sim/adapter/regression), marker `hw`, fixture, aturan determinisme. Direktori placeholder `tests/sim|adapter|regression/.gitkeep` dibuat (make test koleksi bersih).
  - README utama — section "Development" (target make + pointer tests/README.md).
- **Acceptance (fresh-ish, offline):** `make setup` OK · `make lint` OK · `make test` **84 passed (0.80 s)** · `record-fixture` stub OK. Verifikasi exit criteria sprint: invalid config → **exit 5**, version/validate exit 0, grep gate CLEAN, PRD+ADRs committed.
- **Issues ditemukan:** tidak ada.
- **Perubahan state:** task selesai 8 → 9 (R-009 done) · **Sprint 1 (M0) → `COMPLETE`** (9/9, semua exit criteria lolos) · Sprint 2 (M1) **dibuka** `IN PROGRESS` (0/7) · `status.md`/`backlog.md`/sprint files/README index diupdate · Task berjalan dikosongkan (next: A-001).
- **Keputusan/ADR:** — (tidak ada; coverage enforcement 85% didefer ke M6 sesuai exit criteria sprint 1).

### Laporan akhir Sprint 1 — M0: Repository / Architecture

- **Completed tasks (9):** R-001 monorepo skeleton (git init, README dua-fase, LICENSE, dirs) · R-002 package Python stdlib-only + toolchain (pyproject, entry points `creature`/`pokedex`, pytest) · R-003 config system (layered, validated, exit 5) · R-004 structured logging (stderr, format `HH:MM:SS.mmm LEVEL component message`, `-v`) · R-005 clock abstraction (`Clock`/`SystemClock`/`SimClock`, determinism backbone) · R-006 seeded RNG (`SeededRng`, per-tick stability, deterministik lintas proses) · R-007 error taxonomy (`LabError`+kind, `to_exit_code`, konsolidasi ConfigError) · R-008 docs skeleton + ADR-001..008 + template · R-009 dev runner + lint gates (Makefile, setup.sh, hygiene lint, tests/README.md).
- **Failed tasks:** tidak ada.
- **Tests:** 84 passed (unit+smoke) · lint (compileall + src hygiene) hijau · semua offline tanpa device/network.
- **Discovered issues:** (1) checkbox R-004 salah centang oleh commit docs R-003 tanpa implementasi → dikoreksi & diimplementasi (dikonfirmasi user); (2) docstring memuat token banned API → tertangkap lint/hygiene test → reword; (3) index sprints README stale (pra-perbaikan Sesi 2).
- **Architecture changes:** tidak ada (ADR-001..008 = baseline decisions PRD §0; M0 murni eksekusi rencana).
- **Remaining work:** M1..M14 (97 task).
- **Next sprint recommendation:** Sprint 2 (M1 — Android Connection Layer): A-001 AdbClient wire wrapper → A-002 discovery → A-003 state machine → A-004 getprop → A-005 fixture transport → A-006/A-007 adapter+failure tests. Device vivo V2157 (serial `34454119440004U`) tersedia sebagai target; M1 tetap dikerjakan offline-first via fixture/mock per PRD.
