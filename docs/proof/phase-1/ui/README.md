# Bằng chứng HUD (client/ui, Nhài)

Chụp bằng Chrome headless, cửa sổ 1400×800, client `chonoi/web/index.html` ở commit `640d03e` (nhánh `p1/ui-nhai`, đã gộp lát 3 và 4 từ `main`).

## Buổi tối: số thật từ sim của lát 3 và 4
Cách tạo: chạy `runner.Session("quan", …, seed 3)` với kho `{ca_loc:2, ca_linh:3, bong_dien_dien:1, bong_sung:4}`. Một bot đơn giản lái Út Sen đi qua các bước nấu → bưng → dọn. Snapshot thật ở từng mốc được đưa vào client để vẽ.

Chuỗi sự kiện thật:
- t120 `customer_arrived`
- t214 `cook_started`
- t574 `dish_ready`
- t575 `dish_picked`
- t700 `served` (boa 12k)
- t1300 `paid` (72k)

| Ảnh | Tick | HUD cho thấy |
|---|---|---|
| [quan-1-khach-den.png](quan-1-khach-den.png) | 120 | Khách T1 gọi cá lóc nướng trui; kho khả dụng `cá lóc 1 (giữ 1)`; kiên nhẫn 60s; Má Tư mở đầu |
| [quan-2-dang-nau.png](quan-2-dang-nau.png) | 375 | Bếp B1 đang nấu, có vòng tiến độ và khói; đơn ở trạng thái "đang làm"; gợi ý "còn 4s" |
| [quan-3-bung-mon.png](quan-3-bung-mon.png) | 575 | Trên tay `Cá lóc nướng trui (đơn C1)`; thông báo "đã chín" và "Bưng…" |
| [quan-4-tra-tien.png](quan-4-tra-tien.png) | 1300 | Tiền 72k, uy tín 3.2, điểm 372; thông báo "Thu 72k (gồm boa 12k)" |

Ảnh 3 cho thấy lỗi gợi ý "B1: chưa có đơn để nấu" lúc đang bưng món. Lỗi đã sửa ở `640d03e`: gợi ý mới là "Đang bưng …, ra bàn T1 dọn cho khách".

## Buổi sáng: snapshot giả
[gather-hud.png](gather-hud.png): lát 1 và 2 chưa gộp, nên oxy, Máu, giỏ và sự kiện `fish_caught` trong ảnh là **dữ liệu giả** dựng tay theo đúng tên trường của Test Contract. Ảnh dùng để kiểm bố cục, hình cá và trang trí. Sẽ chụp lại bằng số thật khi lát 1 và 2 vào `main`.
