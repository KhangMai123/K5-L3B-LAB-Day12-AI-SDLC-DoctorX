# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11/2026 | Khách đến nhưng không có món đủ nguyên liệu có chiếm bàn không? | Giả định: Không tạo khách, không chiếm bàn, phát `no_dish`. | PO – Minh |
| 2 | 21/11/2026 | Nhiều khách đến cùng tick thì thứ tự xử lý thế nào? | Giả định: Xử lý theo ID khách tăng dần. | PO – Minh |
| 3 | 21/11/2026 | ID khách mới có định dạng bắt buộc không? | Giả định: Sinh ID C1, C2... không trùng fixture. | Minh + Diệp |
| 4 | 21/11/2026 | Khách rời đi khi món đã trên tay thì xử lý thế nào? | Theo Test Contract: Hủy món, không hoàn nguyên liệu đã tiêu thụ. | Minh + Diệp |
| 5 | 21/11/2026 | Scenario có khách và đơn sẵn thì có tạo lại đơn không? | Không tạo lại; giữ nguyên fixture, suy ra reserved khi thiếu theo contract. | Minh |

