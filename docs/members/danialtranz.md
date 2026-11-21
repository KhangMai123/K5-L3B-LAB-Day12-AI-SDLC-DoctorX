# danialtranz — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): Lát 1 trong `chonoi/sim/gather.py` — dive/surface, oxy, ngạt/choke, ngất/faint, API giỏ `can_hold`/`push_hold`; test `tests/test_gather_lat1.py`; Scrum cập nhật `CHANGELOG.md` / `docs/standup.md`.
- Tôi đã review (kèm link): sẽ review chéo Lát 2 với Phát khi có PR.
- AI sai ở đâu và tôi phát hiện thế nào: cần chốt timing ngạt (t+59) và nổi đúng bước ngạt thì không choke — đã khóa bằng test.
- Điều tôi học được: đọc số từ `game.contract.json`, không hard-code; chốt API giỏ sớm để Lát 2 ghép được.

## Phase 2–3

- Được giao (xem `TEAM.md`): P2-B Cá Sấu, Máu, ngất; P3 hao tươi giỏ (cùng Phát); Scrum giữ `CHANGELOG.md`, `docs/standup.md`.
- Đã làm (commit): `0a725a8` (đưa phần lớn code P2–P4 vào `main`: `sim/day.py`, cá bơi/sinh, Cá Sấu, độ tươi, `bench`/`soak`, 2 skill `.agents/skills/`), `921f3a8` (live/HUD chế độ day, nhập Shop), `3e05e0c` (web).
- Cần xử lý: `921f3a8` đổi `first_customer_tick` 60 / `customer_interval_s` 8, lệch số chuẩn ticket P2 (120 / 15 s) → test đỏ; phối hợp Minh trả lại.
- Tôi đã review: *(tự điền)*
- AI sai ở đâu và tôi phát hiện thế nào: *(tự điền)*
- Điều tôi học được: *(tự điền)*
