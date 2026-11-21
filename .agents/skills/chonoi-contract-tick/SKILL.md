---
name: chonoi-contract-tick
description: >-
  Áp Test Contract khi sửa một bước sim (thứ tự tick, event, snapshot, RNG Streams).
  Dùng trước/khi viết luật gather/quan/day hoặc sửa test theo AC.
---

# Luật một bước (Test Contract)

## Bắt buộc
1. Số liệu chỉ đọc từ `game.contract.json` / scenario — không hard-code.
2. RNG chỉ qua `Streams` (`chonoi/rng.py`); không `random`, không đồng hồ hệ thống.
3. Sắp thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.
4. Bước k đọc frame tick=k, biến trạng thái k→k+1, ghi event tại k+1.

## Gather (thứ tự rút gọn P1)
Đồng hồ/cooldown/hồi nút → bơi + oxy/ngạt → interact (bến trước hái) → catch → hết giờ → (P2: cá bơi/sinh sau nếu còn giờ).

## Quán (thứ tự rút gọn P1)
Đồng hồ/timer nấu-ăn-kiên nhẫn → (P3: hao tươi) → di chuyển + tối đa 1 interact → thanh toán/rời → sinh khách nếu còn giờ.

## Event / snapshot
- Xuất tọa độ 3 chữ số thập phân; tiền/điểm/id so chính xác.
- Điểm: `earned + 100 * floor(reputation)`.
- Không đổi kết quả headless bằng UI/mở rộng sáng tạo.

## Trước khi sửa test cho xanh
Sửa luật hoặc ghi lý do đổi test trong commit/`docs/clarify.md`. Không “vá test” khi luật sai.
