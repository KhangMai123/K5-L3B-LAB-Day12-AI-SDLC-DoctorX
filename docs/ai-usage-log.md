# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Diệp | Claude Code (Opus 5.5) | Soạn `docs/contracts/README.md` (kho, sim↔UI, sự kiện) từ code khung + HUD của Nhài; gộp `main`; chạy test + smoke 2 tiến trình | ~1 phiên, không đo token | AI không đọc được PRD-0 (lab board khóa theo giờ) nên tự đặt dạng `hand`/`stove.dish` → đánh dấu [GĐ], chuyển PO xác nhận (clarify #6). Ban đầu báo 20 test đỏ: thật ra do Windows không có `python3`, chạy lại với `python3` thì 32/32 xanh |
| 1 | Diệp | Claude Code (Opus 5.5) | Lát 4 `chonoi/sim/quan.py` (bếp, bưng, phục vụ, boa, trả tiền, uy tín, hủy món khi khách bỏ đi) + `tests/test_quan_lat4.py` (12 test) + proof headless | ~1 phiên, không đo token | Kịch bản input headless do AI tự viết 2 lần đặt sai đường đi (đứng ngoài `interact_radius`), phát hiện nhờ đọc `player.pos` trong snapshot; luật không sai. Thời điểm cộng `tip_reputation` là giả định → clarify #7 |
