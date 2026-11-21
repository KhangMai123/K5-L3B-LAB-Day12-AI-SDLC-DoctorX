# Credits
Liệt kê asset ngoài (nguồn, giấy phép CC0/CC-BY/MIT) và công cụ AI đã dùng.

## Hình ảnh (`chonoi/web/assets/`, chỉ dùng ở cửa sổ chơi, headless không tải)

Nguồn: bộ "Fish" (21 hình) tải từ clker.com, danh sách link gốc nằm trong `References.txt` của gói. Clip art trên clker.com là **public domain**. Nhóm đổi tên file và nhuộm màu bằng CSS filter lúc vẽ; file gốc giữ nguyên.

| File trong repo | File gốc trong gói | Tác giả (theo tên file) | Dùng làm |
|---|---|---|---|
| `ca_loc.png` | `11954412511420549680molumen_Fish_.svg.med.png` | molumen | cá lóc (nhuộm sẫm màu rêu) |
| `ca_linh.png` | `1322601728964270501Generic Fish.svg.med.png` | (không ghi) | cá linh (nhuộm bạc) |
| `rong.png` | `1197097133372198046johnny_automatic_seaweed.svg.med.png` | johnny_automatic | rong đáy sông |
| `oc.png` | `13280382821221522943Snail Shell.svg.thumb.png` | (không ghi) | vỏ ốc đáy sông |
| `rua.png` | `11949837491674168150turtle_jurgen_gaeremyn_01.svg.med.png` | Jurgen Gaeremyn | rùa bơi ở đáy |

### Nhân vật quán (Phase 2, nhánh `p2/asset`)

| File | Kích thước | Dùng làm | Nguồn |
|---|---|---|---|
| `customer_wait.png` | 256×256 | khách đang chờ (bong bóng đồng hồ) | Nhài cung cấp |
| `customer_eat.png` | 256×256 | khách đang ăn | Nhài cung cấp |
| `customer_angry.png` | 256×256 | khách mất kiên nhẫn | Nhài cung cấp |
| `ut_sen_top.png` | 256×256 | Út Sen bưng khay | Nhài cung cấp |
| `warn_customer.png` | 128×128 | icon cảnh báo khách sắp bỏ đi | Nhài cung cấp |

> **Cần bổ sung trước khi gộp:** công cụ hoặc trang đã tạo/tải 5 ảnh này, và giấy phép (CC0/CC-BY/MIT hoặc nhóm tự tạo).
>
> Xử lý của nhóm: ảnh gốc là ảnh chụp màn hình có nền ô caro in sẵn. Nhóm đã xóa nền bằng flood-fill từ mép, bỏ mảnh vụn và viền khung, cắt sát, rồi đưa về khung vuông trong suốt.

Các hình còn lại (nhà sàn, Út Sen, Má Tư, bông súng, bông điên điển, bếp, bàn, đèn dây) do nhóm tự vẽ bằng canvas trong `chonoi/web/index.html`.

## Shop cuối ngày

`shop_bg.png`, `upgrade_oxygen_1.png`, `upgrade_oxygen_2.png`, `upgrade_hp_1.png`, `upgrade_hp_2.png`, `btn_buy.png`, `btn_done.png` và `icon_money.png` là hình tạo bằng OpenAI ImageGen cho quầy Má Tư. Các PNG vật phẩm, nút và icon tiền có nền trong suốt. Chữ nút và đơn vị tiền được hiển thị bằng UI.

## Asset CHƯA ghi nguồn / giấy phép (rà lúc phát hành v1.0.0)

Rà bằng cách đối chiếu từng file trong `chonoi/web/assets/` với file này. Các file dưới đây có trong repo nhưng chưa ghi nguồn; **người đã thêm phải bổ sung nguồn + giấy phép (CC0/CC-BY/MIT hoặc tự tạo/công cụ tạo ảnh)**, nếu không xác minh được thì thay bằng hình nhóm tự vẽ.

| File | Người thêm (commit) | Dùng làm |
|---|---|---|
| `dish_ca_keo_nuong.png`, `dish_ca_loc_nuong_chui.png`, `dish_canh_chua_ca_loc.png`, `dish_lau_ca_linh_dien_dien.png`, `dish_lau_mam.png` | Minh (`685a1b9`) | icon món trong HUD quán |
| `dish_goi_bong_sung.png` | Minh (`fe794f1`) | icon món |
| `fish_catcher.png` | Hưng (`921f3a8`) | hình Út Sen bắt cá |
| `stove_idle.png`, `stove_cook.png`, `stove_ready.png`, `table.png` | Diệp (`e41c329`) | bếp 3 trạng thái, bàn |

## Công cụ AI
- Claude Code (Claude Opus 5.5): HUD, đồ họa vector, thoại Má Tư; chi tiết ở `docs/ai-usage-log.md`.
- Claude Code (Claude Opus 5.5) cùng Diệp: lát 4, hợp đồng, mở rộng `net`/`current`/`leaderboard`, pause, soak/bench, bằng chứng Phase 2–4.
- OpenAI ImageGen: hình Shop (xem mục Shop cuối ngày).
