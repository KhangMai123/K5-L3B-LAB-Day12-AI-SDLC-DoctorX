# nhaipt342k4 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Module `client/ui`: HUD 2 buổi theo PRD-0 (`d853e11`).
  - Mở rộng #1 "Lời Má Tư", thoại giọng Nam Bộ chỉ chạy ở client (`c14a6ce`).
  - Vẽ cá, bông, đáy sông; ảnh public domain có ghi CREDITS (`2fd2a51`, `a6afa97`).
  - Kiểm HUD bằng số thật cả 4 lát, sửa gợi ý (`640d03e`, `793287d`); bằng chứng ở `docs/proof/phase-1/ui/`.
- **Tôi đã review (kèm link):** [PR #3](https://github.com/KhangMai123/K5-L3B-LAB-Day12-AI-SDLC-DoctorX/pull/3), lát 2 của Phát. `hold_full` thiếu `action` và `node_id`/`fish_id` so với PRD mục E.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Chạy `python3` trên Windows nên báo 20 lỗi giả; đọc log thì thấy do môi trường.
  - Tự thêm dòng đồng tác giả Claude vào commit; tôi thấy trên GitHub, yêu cầu bỏ.
  - Ảnh "đang nấu" hiện khách "đang ăn" do snapshot dính tham chiếu; so với số in ra thì thấy.
- **Điều tôi học được:** UI chỉ đọc snapshot thì sáng tạo thoải mái mà không phá headless; chốt tên trường sớm giúp HUD khớp ngay khi gộp.
