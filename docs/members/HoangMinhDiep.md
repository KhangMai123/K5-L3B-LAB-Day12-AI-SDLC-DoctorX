# HoangMinhDiep — phản tư cá nhân (≤ 200 từ)

> Integrator (trưởng nhóm) + Lát 4.

- **Tôi đã làm:** P1 chốt hợp đồng `docs/contracts/` (`5e9598f`), Lát 4 bếp/bưng/phục vụ/tiền/uy tín (`9936c76`), kéo code Lát 3 về khớp hợp đồng (`d862253`). P2–P4 rà `main` rồi sửa lệch ticket: lịch khách, vỏ event day, pause 3 mode, recoil Cá Sấu, soak, bench. Làm mở rộng `net`, `current`, `leaderboard`, phụ đề SFX, HUD độ tươi. Viết `tools/make_proof.py`, ma trận P2–P4, release notes, gắn tag.
- **Đã giúp ai:** Minh (sửa `stock`/`no_dish`/`customer_left` của Lát 3), Nhài (tên trường HUD; sửa HUD giỏ vỡ với v1.2), Hưng (sửa số khách và recoil trong commit P2–P4).
- **AI sai ở đâu:** báo 20 test đỏ, thật ra do Windows thiếu `python3`. So độ tươi bằng `==` nên báo bàn giao hỏng. Viết fixture cho người chơi lặn tới ngất rồi tưởng là lỗi luật. Ghi "đã báo nhóm" khi chưa báo. Tôi đọc log, đọc tick và số thật để bắt từng lỗi.
- **Bài học:** test chỉ bắt được cái mình nghĩ tới. Chạy thật để tạo bằng chứng mới lộ ra lỗi lệch ticket. Lỗi nào cũng cần một test đỏ trước khi sửa.
