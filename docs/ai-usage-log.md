# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Diệp | Claude Code (Opus 5.5) | Soạn `docs/contracts/README.md` (kho, sim↔UI, sự kiện) từ code khung + HUD của Nhài; gộp `main`; chạy test + smoke 2 tiến trình | ~1 phiên, không đo token | AI không đọc được PRD-0 (lab board khóa theo giờ) nên tự đặt dạng `hand`/`stove.dish` → đánh dấu [GĐ], chuyển PO xác nhận (clarify #6). Ban đầu báo 20 test đỏ: thật ra do Windows không có `python3`, chạy lại với `python3` thì 32/32 xanh |
