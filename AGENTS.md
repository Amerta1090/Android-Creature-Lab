# Android Creature Lab — Panduan untuk Agent AI

Proyek ini dikembangkan secara iteratif lewat protokol `prompt.md`.

- **MULAI DI SINI:** baca `prompt.md` dan ikuti seluruh isinya.
- **State (source of truth):** `docs/status.md`
- **Plan:** `docs/PRD.md` (PRD + backlog lengkap §O)
- **Sprints:** `docs/sprints/` (sprint aktif = yang belum `COMPLETE`)
- **Backlog master:** `docs/backlog.md`
- **Log sesi:** `docs/session-log.md`

Aturan inti:
- Eksekusi inkremental per protokol — jangan mendesain ulang proyek.
- DoD setiap task wajib terpenuhi sebelum ditandai selesai.
- Konfirmasi ke user untuk perubahan arsitektur, dependency baru, atau penambahan scope.
- Determinisme (injected clock + seeded RNG) dan stdlib-first adalah batasan mengikat dari PRD.