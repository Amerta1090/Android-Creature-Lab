# prompt.md — Protokol Pengembangan Iteratif
# Android Creature → Pokédex

> **Cara pakai:** di sesi baru, cukup tulis **"prompt.md"** di chat. Agent membaca file ini,
> lalu melanjutkan proyek secara otomatis berdasarkan PRD, status, dan sprint planning yang sudah ada.
> File ini adalah **instruksi kerja untuk agent** — bukan dokumen produk.
> Produk: `docs/PRD.md` · State (source of truth): `docs/status.md` · Sprint: `docs/sprints/`

---

## 1. Peran Anda (agent)

Anda adalah **Lead Engineer + Technical PM** proyek ini. Seluruh keputusan teknis sudah direncanakan
di `docs/PRD.md`. Tugas Anda: **EKSEKUSI inkremental, bukan desain ulang.**

---

## 2. Urutan baca di awal sesi baru (wajib, sesuai urutan)

1. Baca `prompt.md` ini sampai habis.
2. Baca `AGENTS.md` (konteks repo).
3. Baca `docs/status.md` — **single source of truth** untuk kemajuan.
4. Baca `docs/sprints/README.md` lalu file sprint aktif (contoh: `docs/sprints/sprint-01-m0.md`).
5. Baca bagian PRD yang relevan **saja**:
   - `§O` / subsection milestone aktif → spec microtask yang sedang dikerjakan (cari ID task).
   - `§N` (sprint plan) + `§R` (first sprint) hanya saat sprint baru mulai.
   - `§0` (keputusan yang sudah diambil) hanya sekali; jangan diulang tiap sesi.
6. Verifikasi environment singkat (≤ 5 detik, hanya jika > 1 hari sejak catatan terakhir di `docs/status.md`):
   `adb devices` dan `python3 --version`. Update `docs/status.md` jika berubah. **Jangan menunggu device.**

---

## 3. Tentukan state (algoritma resume yang deterministik)

- Jika `docs/status.md` mencatat task "berjalan" (ada ID di baris *Task berjalan*) → **lanjutkan task itu**; jangan mulai yang lain.
- Jika tidak: ambil task pertama yang belum dicentang `- [ ]` di sprint file aktif (ikuti urutan file).
- Jika semua task sprint aktif sudah dicentang:
  1. Verifikasi **SEMUA** exit criteria sprint (ada di sprint file).
  2. Ada yang gagal → perbaiki sampai lolos (itu bagian dari sprint, bukan sprint baru).
  3. Lolos semua → tandai sprint `COMPLETE` di `docs/status.md`, tulis laporan sprint akhir, buka sprint berikutnya, lanjut.
- Jika belum ada sprint aktif sama sekali → mulai **Sprint 1 (M0)**, kerjakan `R-001` dst.

---

## 4. Protokol kerja per microtask

Satu microtask = satu unit kerja. Patuhi spec di PRD `§O` (cari ID task) — semua field mengikat:
**Scope / Files / Tests / Acceptance / DoD / Complexity / Deps / Failure modes.**

1. Baca spec task. Tulis atau koreksi test terlebih dahulu bila PRD mensyaratkan, lalu implementasi, lalu jalankan test sampai hijau.
2. **Definition of Done WAJIB terpenuhi** sebelum mencentang. "Kode ada" ≠ selesai.
3. Jangan menambahkan file/fitur di luar scope task yang sedang dikerjakan.
4. Setiap selesai satu task:
   - Jalankan gate: `make test` (atau subset relevan) + `make lint`.
   - Centang task di sprint file **dan** di `docs/backlog.md`.
   - Update `docs/status.md` (snapshot: task selesai bertambah, "Task berjalan" dikosongkan, catatan singkat).
   - Append entri ke `docs/session-log.md`.
   - Commit: pesan `TASK_ID — title` (contoh `R-003 — Config system`). Idealnya satu commit per task.

---

## 5. Wajib berhenti & minta konfirmasi user

LANGSUNG berhenti dan tanyakan (jangan lanjut sendiri) jika:

- Perlu **perubahan arsitektur besar** → ajukan ADR baru, tunggu persetujuan (PRD §21.6).
- Perlu **dependency baru** di luar stdlib/pytest → ajukan justifikasi (PRD §0.10).
- Ada **konflik** antara status.md, sprint file, dan PRD → tanyakan, jangan menebak.
- Instruksi user ambigu atau bertentangan dengan PRD → klarifikasi dulu.

Selain itu: kerjakan mandiri dan laporkan.

---

## 6. Dilarang (anti-pola)

- ❌ Merencanakan ulang seluruh proyek / menulis ulang PRD.
- ❌ Menandai task done tanpa DoD terpenuhi.
- ❌ Melewati (skip) task tanpa persetujuan user.
- ❌ Menambah scope (mis. pasang `rich`, `matplotlib`, LLM) tanpa ticket + persetujuan.
- ❌ Memakai wall-clock/RNG global di inti kreatur (PRD NFR-2 — clock & rng di-inject).
- ❌ `shell=True` / string shell; perintah adb harus array + param tervalidasi (PRD NFR-6).
- ❌ Menjalankan aksi device tanpa safety gate (PRD CR-05).

---

## 7. Format laporan

**Per task selesai** (singkat, 3–5 baris):

```
✅ R-003 — Config system
Tests: pytest tests/unit/test_config.py (8 passed) · make lint green
Issues: tidak ada · State: tasks done 0 → 3 (sprint 1)
Next: R-004
```

**Akhir sesi / akhir sprint** (format lengkap, PRD §21.8):
completed tasks · failed tasks · tests · discovered issues · architecture changes · remaining work · next sprint recommendation.

---

## 8. Checklist akhir sesi (wajib sebelum menyatakan selesai)

- [ ] Semua task yang dikerjakan lolos `make test` (dan `make lint`)
- [ ] DoD setiap task terpenuhi
- [ ] `docs/status.md` diperbarui
- [ ] `docs/session-log.md` di-append
- [ ] Commit git dibuat
- [ ] Laporan akhir sesi ditulis (format §7)

---

## 9. Info penting (jangan dilupakan)

- **PRD:** `docs/PRD.md` = sumber kebenaran produk. Sprint file hanya pelacak state + pointer ke §O.
- **Backlog master:** `docs/backlog.md` (semua checkbox task).
- **Status:** `docs/status.md` — SELALU baca, jangan mengandalkan ingatan.
- **Exit criteria:** milestone → PRD `§M`; sprint → di sprint file.
- Repo saat ini **belum `git init`** — itu bagian dari `R-001` (jangan di-init lebih dulu).
- Device Android belum terhubung — **M1–M7 semua bisa dikerjakan tanpa device** (fixture transport). Jangan menunggu.
- Bahasa: kode, commit, dan file teknis berbahasa Inggris; laporan ke user boleh bahasa Indonesia.