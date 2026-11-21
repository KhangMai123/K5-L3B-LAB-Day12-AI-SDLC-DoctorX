# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-L2-1 | 2026-11-21 | Cooldown bắt cá có bắt đầu khi bắt hụt hoặc giỏ thiếu chỗ không? | Theo PRD-0 mục F Gather: chỉ đặt cooldown khi bắt thành công (`fish_caught`). Hụt/`hold_full` giữ đàn và cooldown cũ. | Chốt theo PRD-0 (PO) |
| P1-L2-2 | 2026-11-21 | Payload sự kiện Lát 2 là gì? | `gather {node_id, kind, amount}`, `fish_caught {fish_id, kind, yield}`, `hold_full {action, node_id\|fish_id, required, free}`. | docs/contracts + PRD-0 E |
| 1 | 21/11/2026 | Khách đến nhưng không có món đủ nguyên liệu có chiếm bàn không? | Không tạo khách, không chiếm bàn, phát `no_dish`. | PO – Minh |
| 2 | 21/11/2026 | Nhiều khách đến cùng tick thì thứ tự xử lý thế nào? | Xử lý theo ID khách tăng dần. | PO – Minh |
| 3 | 21/11/2026 | ID khách mới có định dạng bắt buộc không? | Sinh ID C1, C2... không trùng fixture. | Minh + Diệp |
| 4 | 21/11/2026 | Khách rời đi khi món đã trên tay thì xử lý thế nào? | Hủy món, không hoàn nguyên liệu đã tiêu thụ. | Minh + Diệp |
| 5 | 21/11/2026 | Scenario có khách và đơn sẵn thì có tạo lại đơn không? | Không tạo lại; giữ fixture, suy reserved khi thiếu. | Minh |
| 6 | 21/11/2026 | `hand` và `stove.dish` dạng gì? | `hand = null` hoặc `{"order_id","dish_id","base_price"}`; `stoves[].dish = null` hoặc `{"dish_id","order_id"}`; `order_id = id khách`. | PRD-0 D |
| 7 | 21/11/2026 | `tip_reputation` cộng lúc nào? Interact thất bại có thử đối tượng kế? | Cộng lúc `paid` khi tip > 0, kẹp uy tín. Interact chỉ 1 đối tượng gần nhất (khoảng cách, bếp trước bàn, id); không được thì bỏ lượt. | PRD-0 F Quán |
| 8 | 21/11/2026 (P2) | Mốc khách `120 + 900·k` tới mà bàn đầy thì sao? | Theo TICKET-02 1.3 "nếu có bàn trống": bỏ lượt, cộng tiếp 900 tick; `no_dish` cũng tiêu lượt. Trả `first_customer_tick` 120 / `customer_interval_s` 15 (921f3a8 đã đổi 60 / 8 để chơi nhanh). | Diệp (Integrator), theo ticket |
| 9 | 21/11/2026 (P2) | Event tick 0 của `--mode day` đứng trước hay sau snapshot tick 0? | Sau: giữ Contract B (snapshot tick 0 là dòng đầu), rồi `day_start → day_plan → phase_start(gather)` mang tick 0, phase gather, day 1 (đúng dòng mẫu ticket). | Diệp — giả định, chờ PO đối chiếu máy chấm |
| 10 | 21/11/2026 (P2) | Các mục mở rộng "nhóm 6 ít nhất 2 mục" tính theo phase hay cả lab? | Ticket ghi "Kỳ vọng tính cả buổi lab" → tính cộng dồn. Nhóm có `burn`, `net`, `current`, `leaderboard` (+ phụ đề SFX). | Diệp đọc ticket; PO xác nhận |
| 11 | 21/11/2026 (P4) | `bench_cmd` "có render" khi UI là canvas trong trình duyệt? | Python stdlib không vẽ được canvas; mỗi khung đo bước sim + snapshot + JSON như `GET /state`. Ghi là giới hạn trong README/release notes. | Diệp — giới hạn đã biết |
| 12 | 21/11/2026 (P4) | Soak dùng bot nào? | Bot tất định không RNG: giữ `interact` ở pha gather (cập bến ngay), quán chạy hết ca, giữ `shop_done` ở Shop. Một DaySim liền N Ngày; kế hoạch D1–D5 lặp. | Diệp |
| 13 | 21/11/2026 (P4) | Store xếp hạng mặc định ở đâu? | `~/.chonoi-doctorx/leaderboard.json` khi không truyền `--leaderboard`; test luôn dùng store riêng. | Diệp |
