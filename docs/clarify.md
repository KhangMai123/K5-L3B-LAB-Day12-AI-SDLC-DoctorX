# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-L2-1 | 2026-11-21 | Cooldown bắt cá có bắt đầu khi bắt hụt hoặc giỏ thiếu chỗ không? | Tạm triển khai chỉ bắt đầu khi `fish_caught`; hụt/`hold_full` giữ nguyên đàn và không đặt lại cooldown. Đã hỏi người dùng, chờ PO đối chiếu PRD-0. | Chờ PO (Minh) |
| P1-L2-2 | 2026-11-21 | Payload sự kiện Lát 2 là gì? Repo chưa có bản PRD-0 đầy đủ và bảng sự kiện trong `docs/contracts/` chưa được chốt. | Tạm dùng `gather {node_id, kind, count}`, `fish_caught {fish_id, kind, count}`, `hold_full {kind, needed, free}`. Không sửa hợp đồng khóa; cần Integrator xác nhận trước tích hợp. | Chờ PO / Integrator |
