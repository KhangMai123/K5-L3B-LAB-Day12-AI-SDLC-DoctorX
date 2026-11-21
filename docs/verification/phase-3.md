# Ma trận truy vết Phase 3 — TICKET-03 "Mùa Nước Nổi" (Test Contract v1.2)

**Commit gắn tag `phase-3`:** commit thêm `test_fresh_rules_p3` sau HUD độ tươi — hash ghi ở `docs/proof/phase-4/tags.log`. Bộ test chạy lại tại tag trong worktree sạch. Tag gắn **muộn** sau hạn 2:30.

## Tác động & thứ tự tích hợp (đã làm)

| Module | File | Test giữ / đổi / thêm | Người |
|---|---|---|---|
| Adapter kho | `chonoi/inventory.py`, `contract.py`, `docs/contracts/` | Đổi: kho đếm → mã 2; thêm `test_fresh_p3`; `inventory.sample.json` sang v1.2 | Hưng (code `0a725a8`), Diệp (hợp đồng, mẫu) |
| Lặn | `chonoi/sim/gather.py` | `test_fresh_p3` (ngưỡng), `test_ext_current` | Hưng; Diệp (`current`) |
| Quán | `chonoi/sim/quan.py` | `test_quan_p1`, `test_quan_lat4` (giữ chỗ theo id, giá theo tươi) | Hưng (code), Khang (test P1) |
| Day | `chonoi/sim/day.py` | `test_day_envelope.test_next_day_hold_gets_new_ids_in_array_order` | Diệp |
| HUD | `chonoi/web/index.html` | `test_live` | Diệp |

Thứ tự: schema/adapter + test migration → Lặn, Quán → HUD → bật v1.2 → smoke file + day.

| AC | Yêu cầu | Kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P3-01 | Kho cá thể `{id,kind,fresh}`; kho đếm/id trùng/kind lạ/fresh ngoài miền → mã 2 | `test_fresh_p3`, `test_fresh_rules_p3.test_v12_inventory_bad_schemas_exit_2` | `docs/proof/phase-3/handoff.log` (kho đếm v1.0 → exit 2) | ĐẠT |
| AC-P3-02 | Hao tươi giỏ 0.5/s từ bước sau; `spoiled` đúng một lần ở ngưỡng 30 | `test_fresh_p3.test_spoiled_at_threshold_on_first_gather_step` | `docs/proof/phase-3/spoiled-threshold.log` — trùng dòng mẫu ticket | ĐẠT |
| AC-P3-03 | Smoke bàn giao file: `fresh:100`, cập bến frame 0, `quan --ticks 0` khớp id/kind/fresh | `make_proof` | `docs/proof/phase-3/handoff.{log,kho.json}` | ĐẠT (fresh 99.99167 trong file; JSONL ±0.01) |
| AC-P3-04 | Id `I*` tăng xuyên pha và Ngày; Ngày kế cấp id mới cho mẫu `gather.hold` | `test_day_envelope` | `docs/proof/phase-3/day-ids.log` | ĐẠT (trước đó trùng `I1` ở Ngày 2) |
| AC-P3-05 | Giữ chỗ theo id (tươi nhất, hòa theo id); giữ lại một lần khi vừa ươn → `unfulfillable` | `test_fresh_rules_p3` (giữ lại sang `I2`; không có hàng thay → `unfulfillable`, khách vẫn chờ), `test_quan_p1` | — | ĐẠT |
| AC-P3-06 | `base_price = floor(giá × avg fresh / 100)`, boa trên giá đã chốt | `test_fresh_rules_p3.test_base_price_floor_of_list_price_times_avg_fresh` (fresh 50 → 29), `test_quan_lat4` | `cook_started.data.items` | ĐẠT |
| AC-P3-07 | HUD đọc được độ tươi / nhận ra hàng ươn | Chơi thử; `test_live` | thanh tươi từng ô, nhãn "ươn", % ở kho quán | ĐẠT (chưa có ảnh chụp) |
| AC-P3-08 | Mở rộng `current`: lịch 1800·k, báo trước 120, 480 tick, lực khi d ≥ 10, `current_end` elapsed/phase_end | `test_ext_current` (7 test) | — | ĐẠT |
| AC-P3-09 | CHANGELOG ghi breaking change + cách cập nhật fixture | `CHANGELOG.md` mục Phase 3 | — | ĐẠT |
| AC-P3-10 | Regression P1–P2 | `unittest discover` | 149 test OK | ĐẠT |

## Đánh giá ngắn
- Đạt: kho cá thể, ngưỡng, bàn giao file + day, HUD độ tươi, `current`.
- Còn thiếu: mở rộng `reservations` không làm; ảnh chụp HUD.
