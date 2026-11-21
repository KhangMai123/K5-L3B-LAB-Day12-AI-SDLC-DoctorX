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
