# Quán Ăn Chợ Nổi v1.0.0 — nhóm DoctorX

Út Sen lặn bắt cá, hái bông trên sông buổi sáng; tối mở quán trên nhà bè phục vụ khách; cuối ngày mua nâng cấp ở quầy Má Tư. Trọn vòng 5 Ngày, chơi trên trình duyệt, chấm tự động qua headless theo Test Contract v1.3.

## Điểm mới

- **Vòng ngày đầy đủ:** Lặn & Hái → Mở Quán → Shop, kế hoạch món D1–D5 của Má Tư, tiền/uy tín/nâng cấp giữ qua Ngày.
- **Mùa Nước Nổi:** mỗi nguyên liệu có độ tươi riêng, hàng ươn không nấu được, giá món theo độ tươi.
- **Thủy quái:** Cá Sấu Năm Chèo tuần tra và đuổi ở vùng sâu; bị chạm thì mất Máu và rơi hàng.
- **Mở rộng:** cháy món (`burn`), vợt hút cá (`net`), dòng nước lũ (`current`), bảng xếp hạng cục bộ (`leaderboard`), phụ đề SFX.
- **Dễ nhận biết:** cảnh báo bằng chữ + biểu tượng cho oxy cạn, thủy quái gần, khách sắp giận, dòng lũ sắp tới; chế độ tương phản cao (phím **H**); tạm dừng (Esc/P).
- **Đo đạc:** `bench_cmd`, `soak_cmd` (10 Ngày, 0 crash).

## Cách chạy

Cần Python 3.10+ (thư viện chuẩn, không cài thêm gì) và một trình duyệt.

```bash
# từ bản đóng gói: giải nén chonoi-doctorx-v1.0.0.zip rồi
cd chonoi-doctorx-v1.0.0
python3 -m chonoi.live --mode day --days 5      # mở http://127.0.0.1:8000/
```

Hoặc từ clone sạch: xem 3 lệnh ở `README.md`. Phím: WASD bơi/đi · E hái/cập bến/bếp/bàn · Space bắt cá · Shop 1/2/3 mua, E/Enter đóng · Esc/P tạm dừng · H tương phản cao · R chơi lại.

Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` · Headless: `python3 -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --out day.jsonl` · Bench: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` · Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`.

## Giới hạn đã biết

- `bench` đo phía Python (sim + snapshot + JSON cho mỗi khung), **không** đo vẽ canvas/GPU trong trình duyệt.
- Cửa sổ chơi chưa có ô nhập tên cho bảng xếp hạng (ghi qua headless `--days 5`).
- Chưa làm: khách đặt trước (`reservations`), Lao xua, Rắn Hổ Mây, Chợ Chú Sáu, Sổ tay & Cá Hô, Settings âm lượng.
- Một số asset nhân vật/món/bếp chưa ghi nguồn đầy đủ (danh sách trong `CREDITS.md`).
- Bot của `soak` không phục vụ khách (earned = 0); soak kiểm độ bền và tính lặp, không kiểm điểm.
- Tag `phase-1` … `phase-3` được gắn muộn sau hạn giờ; xem `docs/verification/phase-*.md`.

## Bằng chứng

`docs/verification/phase-{1..4}.md` (ma trận AC → bằng chứng → kết quả), `docs/proof/phase-{1..4}/`, `CHANGELOG.md`.
