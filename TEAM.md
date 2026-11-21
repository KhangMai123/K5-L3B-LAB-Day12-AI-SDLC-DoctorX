# TEAM

**Tên nhóm:** DoctorX (`team: "doctorx"`)  **Số người:** 6  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trần Cảnh Hưng - 2A202603759 | danialtranz | `sim/gather` — Lát 1: bơi, oxy, biên, giỏ | Scrum/Release | Lát 2 (Phát) |
| Trương Đức Phát - 2A202603757 | trdphat | `sim/gather` — Lát 2: hái, bắt cá, cập bến, ghi kho | — | Lát 1 (Hưng) |
| Vũ Quang Minh - 2A202603727 | minh240804 | `sim/quan` — Lát 3: khách, giữ chỗ nguyên liệu, kiên nhẫn | PO | Lát 4 (Diệp) |
| Hoàng Minh Diệp - 2A202603764 | HoangMinhDiep | `sim/quan` — Lát 4: bếp, bưng, phục vụ, tiền, uy tín | Integrator (trưởng nhóm) | Lát 3 (Minh) |
| Phùng Thị Nhài - 2A202603725 | nhaipt342k4 | `client/ui` — HUD 2 buổi, `chonoi/web/`, `live.py`; mở rộng #1 | — | UI + chơi thử |
| Mai Xuân Khang - 2A202603722 | KhangMai123 | `qa` — `tests/`, ma trận truy vết, `docs/proof/`; mở rộng #2 | QA lead | `scenario.py` / `contract.py` |

> Mỗi người tự thay `…` bằng GitHub handle của mình (commit đầu tiên). `python3 tools/check_team.py` phải báo OK.

**Vai quy trình:** PO (đầu mối hỏi Anh Năm hàng xóm/giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gộp code, gắn tag `phase-1`) · QA lead (giữ bộ test, `docs/verification/phase-1.md`) · Scrum/Release (giữ mốc thời gian, standup, `docs/standup.md`, `CHANGELOG.md`).

## Chia việc Phase 1 chi tiết

| Người | Việc cụ thể (file chính) | Phụ thuộc | Xong khi |
|---|---|---|---|
| Hưng (Lát 1) | `chonoi/sim/gather.py`: `dive`/`surface` theo biên d ≤ 0.5; oxy theo d cuối bước (+6/tick trên mặt, −1 dưới nước, kẹp); `oxygen_empty`; `zero_oxy_ticks` → `choke` mỗi 60 tick; Máu 0 → bỏ giỏ LIFO, `faint`, `gather_end` fainted, kho rỗng; giỏ theo thứ tự nhặt, trần `hold_capacity` | Khung sẵn có | Test oxy/ngạt/ngất xanh (ngạt lần đầu ở t+59, nổi đúng bước ngạt thì không ngạt) |
| Phát (Lát 2) | `chonoi/sim/gather.py`: hái nút ready gần nhất (chỉ ở mặt nước, hòa theo id) → `gather`, `regrow_ticks`; `node_regrown`; `catch` dưới nước, hết hồi → `fish_caught` + cooldown; `hold_full` (không thử đàn khác); bến xét trước hái; kho khớp `gather_end.inventory` | Giỏ của Hưng (chốt API `hold` trước phút 15) | Smoke `dock.json` ra `catch.json` đúng; ghi kho thật trước phút 25 |
| Minh (Lát 3) | `chonoi/sim/quan.py`: khách fixture từ scenario + suy `reserved`; lịch khách `first_customer_tick` rồi mỗi `customer_interval_s`; bàn trống id nhỏ nhất; chọn đều theo seed trong món đủ kho khả dụng; `no_dish`; giữ chỗ ngay; kiên nhẫn giảm từ bước sau; `customer_left` patience (−0.5 uy tín) / closing | Kho mẫu `docs/contracts/inventory.sample.json` | Khách đến, giữ chỗ, bỏ đi đúng tick |
| Diệp (Lát 4) | `chonoi/sim/quan.py`: tối đa 1 interact chọn theo (khoảng cách, bếp trước bàn, id); bếp idle lấy đơn reserved cũ nhất → `cook_started`; `dish_ready`; `dish_picked` (`carry_limit` 1); `served` + boa `floor(price × 0.2)` nếu kiên nhẫn ≥ 50%; `paid`; tiền/`earned`/uy tín kẹp [0,5]; hết ca → `quan_end`; score | Trạng thái khách/đơn của Minh (chốt tên trường trước phút 15) | Một vòng nấu → bưng → phục vụ → trả tiền đúng event |
| Nhài (UI/HUD) | `chonoi/web/index.html`, `chonoi/live.py`: HUD sáng (thời gian, oxy, Máu, giỏ); HUD tối (kho khả dụng, món gọi, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín); hình khối 2D theo phong cách miền Tây; sau lõi làm **mở rộng #1** (phần thêm phải tắt ở headless) | Snapshot của các lát (đọc trường theo Test Contract E) | Chơi thử 2 buổi trên trình duyệt, HUD đọc được |
| Khang (QA) | `tests/`: test theo từng AC cho 4 lát (viết trước bằng scenario + inputs); smoke 2 tiến trình; kiểm mã thoát 0/1/2; `docs/verification/phase-1.md` + `docs/proof/phase-1/`; bổ sung kiểm fixture trong `scenario.py`/`contract.py` (TODO(nhóm)); sau lõi làm **mở rộng #2** | Có thể bắt đầu ngay từ PRD | Ma trận truy vết đủ AC, kết quả thật lưu trong `docs/proof/phase-1/` |

**Việc chung của từng vai:**
- **PO (Minh):** gom câu hỏi mơ hồ, hỏi Anh Năm, ghi `docs/clarify.md`; chọn 2 mục mở rộng cùng nhóm ở phút 15.
- **Integrator (Diệp):** chốt `docs/contracts/` (file kho + sự kiện/trạng thái sim↔UI) trước phút 15; `team_size`/`team` trong `game.contract.json`; gộp các lát; chạy smoke trên main; gắn và đẩy tag `phase-1` trước 1:00.
- **QA lead (Khang):** giữ bộ test xanh trên main; từ chối gộp nếu test đỏ.
- **Scrum/Release (Hưng):** nhắc mốc phút 15/20/25/45/55; ghi `docs/standup.md`, `CHANGELOG.md`, nhắc mọi người ghi `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.
- **Mọi người:** tối thiểu 3 commit có nội dung từ tài khoản của mình; tự viết `docs/members/<handle>.md`.

## Chia việc Phase 2 (TICKET-02, Test Contract v1.1)

> Code lõi P2 đã vào `main` chủ yếu qua commit `0a725a8` và `921f3a8` (Hưng). Vì vậy mỗi người **nhận quyền sở hữu** một vùng: đọc lại, viết test theo AC, sửa chỗ lệch ticket, lưu bằng chứng. Cặp dự phòng giữ như P1.

| Người | Vùng phụ trách (file chính) | Trạng thái trên `main` | Việc còn lại | Xong khi |
|---|---|---|---|---|
| Phát (P2-A) | `sim/gather.py`: số chuẩn sáng, N5/N6 kèo nèo, `ca_keo` yield 2; cá bơi 1.5 m/s, đổi hướng 120·k, phản xạ mép; sinh 8 đàn đầu ca, trần 12, mỗi 360 tick, trọng số 40/30/30; `fish_spawned`, `age_ticks` | Có code (`0a725a8`) | Test bơi/phản xạ/sinh theo seed; **mở rộng `net`** (chưa có) | Test xanh + `net` khai trong `extensions` |
| Hưng (P2-B, Scrum) | `sim/gather.py`: Cá Sấu M1/M2 (`from_day`), patrol/chase/recoil, ≤ 1 hit/bước, bỏ `floor(n/2)` LIFO, bất tử 90; `monster_hit`, `faint.cause`; scenario `monsters[]` | Có code (`0a725a8`) | Test hit/recoil đúng tick, ngạt + hit cùng tick; trả lại số chuẩn quán đã đổi ở `921f3a8` (xem hàng Minh) | Test xanh; `CHANGELOG.md`, `docs/standup.md` cập nhật |
| Minh (P2-C, PO) | `sim/quan.py`: B2, T2–T4, 6 món; lịch khách `120 + 900·k` khi có bàn trống; đóng ca (khách ăn trả ngay, khách chờ rời không trừ uy tín); lọc menu theo `day_plan`; mở rộng `burn` | Có code; `burn` đã khai | **Lỗi:** `game.contract.json` đang `first_customer_tick: 60`, `customer_interval_s: 8` (đổi ở `921f3a8`), lệch ticket (120 / 15 s) → `test_quan_no_dish_at_scheduled_tick` đỏ. Trả về số chuẩn, kiểm lại luật "bàn đầy giữ mốc lịch"; test `burn` | Suite xanh; clarify ghi quyết định |
| Diệp (P2-D, Integrator) | `sim/day.py`, `runner.py`, `headless.py`: `--mode day --days`, chuỗi pha `day_start → day_plan → phase_start…`, bàn giao kho trong bộ nhớ, Shop (`bought`/`buy_failed`/`shop_end`), `active_upgrades`, `days_completed`; `docs/contracts/` v1.1 | Có code (`0a725a8`) | Rà `day --days 5` (cấp oxy/Máu áp từ Ngày kế, ≤ 20 s); cập nhật hợp đồng v1.1; gộp, chạy smoke trên `main`, gắn tag `phase-2` | Tag `phase-2` trên commit bàn giao |
| Khang (P2-E, QA) | `inputs.py`, `scenario.py`, `tests/`: `pause`/`shop_done`/`buy`, `paused`/`resumed`; scenario khối `day`; regression P1 với số chuẩn | Có `test_day_p2`, `test_contract_and_cli` | Bổ sung test pause và Shop; smoke tích hợp → `docs/proof/phase-2/integration.*` (chưa có thư mục); `docs/verification/phase-2.md` nối đủ AC | Ma trận AC-P2 có bằng chứng thật |
| Nhài (P2-F, UI) | `web/index.html`, `live.py`: menu chính, DayIntro/EveningIntro/DayResult/Shop/Summary, pause Esc/P, HUD mới ("Thủy quái!", "Hết hơi!", cần/đã lấy, màu < 25 %), chữ ≥ 18 px @1280×720 | Có màn day/shop (`921f3a8`, `3e05e0c`), asset (`5537cd7`, `e41c329`, `e8fec51`, `685a1b9`) | Đối chiếu từng mục HUD với ticket; ảnh chụp → `docs/proof/phase-2/ui/`; **mở rộng thứ 2** của P2 nếu `net` không kịp (đề xuất Settings & âm thanh) | Chơi trọn 1 Ngày, có ảnh chứng |

## Chia việc Phase 3 (TICKET-03 "Mùa Nước Nổi", Test Contract v1.2)

> Thứ tự tích hợp để `main` luôn chạy: (1) adapter schema kho + test migration → (2) Lặn và Quán song song → (3) HUD → (4) bật v1.2, smoke file + day → (5) mở rộng. Lõi độ tươi đã vào `main` (`0a725a8`, `tests/test_fresh_p3.py`); các lát dưới đây kiểm theo từng quy tắc của ticket.

| Module | Người | File | Test giữ / đổi / thêm | Việc còn lại |
|---|---|---|---|---|
| Adapter schema kho v1.2 | **Diệp** | `chonoi/inventory.py`, `contract.py`, `docs/contracts/README.md` | Đổi test kho đếm → kỳ vọng mã 2; thêm test id trùng, `fresh` ngoài [0,100], `{"items":[]}` | Hợp đồng v1.2 (kho cá thể, `spoiled`, `cook_started.items`); ghi breaking change trong `CHANGELOG.md` (cùng Hưng) |
| Lặn: hao tươi giỏ | **Hưng** + **Phát** | `sim/gather.py` | Thêm: hao 0.5/s từ bước sau, `spoiled` ở 30 đúng một lần theo id, `lost` là mảng cá thể theo LIFO, id `I*` tăng xuyên pha | Test ngưỡng 30 bằng scenario mẫu của ticket; smoke `fresh:100` + cập bến → `quan --ticks 0` so id/kind/fresh |
| Quán: kho cá thể, giữ theo id, giá theo tươi | **Minh** + **Diệp** | `sim/quan.py` | Đổi: `reserved` là mảng id; thêm: giữ tươi nhất (hòa theo id), giữ lại một lần khi hàng vừa ươn → `unfulfillable`, `base_price = floor(giá × avg fresh/100)`, boa trên giá đã chốt | Test thứ tự trong tick quán (spoiled trước giữ chỗ); **mở rộng `reservations`** (Minh, chưa có) |
| Day: bàn giao trong bộ nhớ | **Diệp** | `sim/day.py` | Thêm: không hao trong tick chuyển pha, id tăng xuyên Ngày | Smoke `day --days 2` lưu `docs/proof/phase-3/` |
| HUD độ tươi | **Nhài** | `web/index.html` | Ảnh chụp (UI không ảnh hưởng headless) | Hiện `fresh` dạng thanh/số + nhãn "ươn" ở giỏ và kho quán (hiện mới có 1 chỗ nhắc `fresh`) |
| QA, migration, bằng chứng | **Khang** | `tests/`, `docs/verification/phase-3.md`, `docs/proof/phase-3/` | Regression P1–P2 còn hiệu lực; ghi lý do mọi test đổi vì luật mới | Ma trận AC-P3 có bằng chứng thật; **mở rộng `current`** (dòng nước lũ, cùng Phát) |

**Mở rộng (nhóm 6 → ≥ 2 mục mỗi phase):** P2 hiện mới khai `burn`; P3 chưa có mục nào. PO (Minh) chốt: P2 thêm `net` (Phát); P3 làm `reservations` (Minh) + `current` (Phát, Khang). Mỗi mục khai trong `extensions`, có test và ghi trong README.

## Mốc thời gian Phase 1 (60 phút)

| Phút | Việc |
|---|---|
| 0–15 | Điền handle, chốt hợp đồng kho + tên trường trạng thái, Khang dựng test khung, các lát bắt đầu song song |
| 20 | Rà lát chậm; người xong trước (thường Nhài/Khang) sang hỗ trợ |
| 25 | Phát xuất file kho thật; Minh/Diệp thử nạp vào quán |
| 30 | Standup 2–3 phút: đã xong / sắp làm / đang vướng |
| 45–55 | Diệp gộp cuối, chạy smoke 2 tiến trình trên main; Khang hoàn thiện ma trận truy vết; cả nhóm chơi thử |
| 55–60 | Dự phòng; Diệp đẩy tag `phase-1` |

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: nhóm chat chung của DoctorX (Zalo/Messenger); việc quan trọng ghi thêm vào issue trên GitHub.
- Khi bất đồng về thiết kế: nói tối đa 2 phút; không xong thì Integrator (Diệp) quyết, riêng chỗ PRD mơ hồ thì PO (Minh) hỏi Anh Năm, rồi ghi lại trong `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh nhóm; người dự phòng ở bảng trên vào pair; quá 20 phút thì người dự phòng nhận tiếp phần việc.
- Giờ standup giữa phase: phút 30 của phase, 2–3 phút, Scrum (Hưng) điều phối.
- Cách đọc code của nhau: review chéo theo cặp dự phòng (Hưng↔Phát, Minh↔Diệp, Nhài↔Khang); xem PR hoặc xem trực tiếp.
- Cách làm việc với Git: nhánh ngắn `p1/<lat>-<ten>` → PR vào `main`, CI xanh và 1 người duyệt; chạy test trước khi đẩy; không sửa `docs/contracts/`, `game.contract.json` khi chưa báo nhóm; chỉ Integrator (Diệp) gắn tag.
