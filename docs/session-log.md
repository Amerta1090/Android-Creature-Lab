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