# Ma trận truy vết Phase 2 — TICKET-02 "Một ngày ở chợ nổi" (Test Contract v1.1)

**Commit gắn tag `phase-2`:** commit sửa recoil Cá Sấu (lõi P2 hoàn tất: lịch khách chuẩn, vỏ event day, pause 3 mode, recoil, `net`) — hash ghi ở `docs/proof/phase-4/tags.log`. Bộ test chạy lại tại tag trong worktree sạch. Tag gắn **muộn** sau hạn 1:55 — ghi trung thực.
Bằng chứng `docs/proof/phase-2/` được tạo lại bằng `python3 tools/make_proof.py` trên commit bàn giao `phase-4` (commit ghi trong từng file log).

| AC | Yêu cầu (ticket) | Kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P2-01 | `contract_version` (≥ 1.1), số chuẩn, 6 nguyên liệu, 6 món, B2, T2–T4 | `test_contract_and_cli` | `game.contract.json` | ĐẠT |
| AC-P2-02 | Cá bơi 1.5 m/s, đổi hướng 120·k, phản xạ mép; sinh 8 đàn đầu ca, trần 12, mỗi 360 tick | `test_day_p2`, `test_gather_p1` | snapshot gather | ĐẠT |
| AC-P2-03 | Cá Sấu M1 (Ngày 1), M2 (từ Ngày 3); hit, bỏ `floor(n/2)` LIFO, bất tử 90, recoil 60 bước lùi xa người chơi | `test_monster_p2` (4 test), `test_day_p2` | commit `gather: Cá Sấu recoil lùi XA người chơi` | ĐẠT — **sửa lỗi** recoil trước đó lùi về phía người chơi (test đỏ trên code cũ) |
| AC-P2-04 | Quán: lịch khách tick `120 + 900·k` khi có bàn trống | `test_python_starter_units.test_quan_no_dish_at_scheduled_tick`, `test_quan_p1` | commit `quan: trả lịch khách về số chuẩn` | ĐẠT (trước đó đỏ do 60 / 8 s) |
| AC-P2-05 | `--mode day`: `day_start → day_plan → phase_start(gather)` ở tick 0; event kết thúc mang pha cũ; `phase_start` pha mới cùng tick | `test_day_envelope` (3 test, đỏ trên code cũ) | `docs/proof/phase-2/day-1.log` | ĐẠT |
| AC-P2-06 | Một Ngày ≤ 22.200 tick, headless ≤ 20 s; `day_plan` D1 đúng | `day-1.log` | `docs/proof/phase-2/day-1.log` (≈ 0.5 s) | ĐẠT |
| AC-P2-07 | Shop: `bought` / `buy_failed`, 600 tick hoặc `shop_done`; cấp mua áp từ Ngày kế | `test_day_p2`, `test_ext_net.test_shop_buys_net_levels_then_max_level` | `docs/proof/phase-2/day-upgrade.log` (oxygen 1 → `oxygen_max_ticks` 2700 ở Ngày 2) | ĐẠT |
| AC-P2-08 | Pause ở cả ba mode: `paused`/`resumed`, `state:"paused"`, `sim_tick`/`phase_tick`/timer đứng yên, bỏ cạnh hành động | `test_pause_p2` (gather, quan, day) | live: `sim_tick` 16 → 16 khi tick 103 → 132 | ĐẠT |
| AC-P2-09 | Smoke tích hợp `gather --inventory-out` → `quan --inventory`, đối chiếu kho tick 0 | `make_proof` | `docs/proof/phase-2/integration.{log,kho.json,quan.jsonl}` | ĐẠT |
| AC-P2-10 | Menu, DayIntro/EveningIntro/DayResult/Shop/Summary, pause menu, HUD (Thủy quái + viền tím, Hết hơi, cần/đã lấy) | Chơi thử trên trình duyệt; `test_live` | `chonoi/web/index.html` | ĐẠT một phần — có màn day/shop, pause, HUD cảnh báo; **chưa có ảnh chụp** trong `docs/proof/phase-2/ui/` |
| AC-P2-11 | Mở rộng (cả lab ≥ 2): `burn`, `net` | `test_quan_p1` (burn), `test_ext_net` (7 test) | `extensions` trong manifest | ĐẠT |
| AC-P2-12 | Regression P1 với số chuẩn, test đổi có ghi lý do | `unittest discover` | commit message các lần đổi test | ĐẠT |

## Đánh giá ngắn
- Đạt: lõi day/shop/pause, số chuẩn, 2 mở rộng P2.
- Lệch phát hiện muộn và đã sửa: lịch khách 60 / 8 s; vỏ event day; pause chỉ có ở day; `sim_tick` nhảy sau pause. Ba lỗi sau không test nào bắt — chỉ lộ ra khi chạy thật để tạo bằng chứng.
- Lỗi recoil (lùi về phía người chơi) lộ ra khi viết test theo đúng câu chữ ticket.
- Còn thiếu: ảnh chụp UI.
