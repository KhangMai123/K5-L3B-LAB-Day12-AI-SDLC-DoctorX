# danialtranz — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Lát 1 trong `chonoi/sim/gather.py` — dive/surface, oxy, ngạt/choke, ngất/faint, API giỏ `can_hold`/`push_hold`; test `tests/test_gather_lat1.py`; Scrum cập nhật `CHANGELOG.md` / `docs/standup.md`.
- Tôi đã review (kèm link): sẽ review chéo Lát 2 với Phát khi có PR.
- AI sai ở đâu và tôi phát hiện thế nào: cần chốt timing ngạt (t+59) và nổi đúng bước ngạt thì không choke — đã khóa bằng test.
- Điều tôi học được: đọc số từ `game.contract.json`, không hard-code; chốt API giỏ sớm để Lát 2 ghép được.
- **P2–P4 (từ git log):** `0a725a8` đưa phần lớn code P2–P4 vào `main` (day/Shop, cá bơi/sinh, Cá Sấu, độ tươi, bench/soak, 2 skill `.agents/skills/`); `921f3a8`, `3e05e0c` cửa sổ chơi chế độ day. Diệp sửa sau đó: số khách 60/8 s → 120/15 s, recoil Cá Sấu ngược hướng. *Đã giúp ai / AI sai / bài học P2–P4: tự điền.*
