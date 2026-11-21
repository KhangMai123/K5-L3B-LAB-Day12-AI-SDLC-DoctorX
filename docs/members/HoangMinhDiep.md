# HoangMinhDiep — phản tư cá nhân (≤ 200 từ)

> Vai: Integrator (trưởng nhóm) + Lát 4 (bếp, bưng, phục vụ, tiền, uy tín). Đang cập nhật trong Phase 1.

- Tôi đã làm (kèm link commit):
  - Chốt hợp đồng tích hợp `docs/contracts/README.md`: file kho, giao diện sim↔UI, danh sách sự kiện (commit `5e9598f`).
  - Gộp `main` (HUD của Nhài) vào nhánh làm việc; chạy 32 test (xanh) + smoke 2 tiến trình gather → kho → quan, kiểm tất định.
  - Kiểm `team`/`team_size` khớp `TEAM.md`; ghi câu hỏi mở clarify #6 cho PO.
  - Lát 4 trên nền lát 3 của Minh: `_interact` (gần nhất, bếp trước bàn, id), `_cook`, `_pick` (carry_limit 1), `_serve` (boa theo kiên nhẫn), `_pay`, `_rep` (kẹp), hủy món khi khách bỏ đi; 12 test `tests/test_quan_lat4.py`; proof `docs/proof/phase-1/lat4/`.
- Tôi đã review (kèm link):
  - Đối chiếu tên trường HUD (`chonoi/web/index.html`, PR #1 của Nhài) với snapshot của khung.
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI báo 20 test đỏ; kiểm lại thì do Windows không có lệnh `python3` (mã 9009), không phải lỗi code. Chạy với `python3` thì 32/32 xanh.
  - AI không đọc được PRD-0 nên tự đặt dạng `hand`/`stove.dish`; tôi bắt đánh dấu [GĐ] và chuyển PO xác nhận.
- Điều tôi học được:
  - Chốt tên trường sớm giúp lát 3, lát 4 và UI làm song song mà không phải chờ nhau.

## Phase 2–3

- Được giao (xem `TEAM.md`): P2-D `--mode day`, Shop, chuyển pha, hợp đồng v1.1, tag `phase-2`; P3 adapter schema kho v1.2, bàn giao trong day, cùng Minh làm quán độ tươi.
- Đã làm (commit): `e41c329` (asset màn 2: bếp idle/nấu/chín, bàn); `202d3a1` (kế hoạch P2, nhánh `p2/plan-diep`); chia việc P2–P3 trong `TEAM.md` (nhánh `p23/team-diep`).
- Phát hiện khi rà `main`: 116 test, 1 đỏ (`test_quan_no_dish_at_scheduled_tick`) do số khách đổi ở `921f3a8`; mở rộng mới khai `burn`, thiếu mục thứ 2 (P2) và chưa có mục nào (P3); chưa có tag `phase-1`/`phase-2` trên remote.
- Tôi đã review: commit `0a725a8`, `921f3a8` (số chuẩn quán, danh sách mở rộng).
- AI sai ở đâu và tôi phát hiện thế nào: *(tự điền)*
- Điều tôi học được: *(tự điền)*
