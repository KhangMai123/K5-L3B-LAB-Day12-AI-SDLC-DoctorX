# Ma trận truy vết Phase 3 — DoctorX

Contract v1.2 — kho cá thể + độ tươi.

| AC | Kiểm chứng | Kết quả |
|---|---|---|
| Schema kho mảng `{id,kind,fresh}`; kho đếm → mã 2 | `test_fresh_p3`, smoke inventory | PASS |
| Hao tươi gather 0.5/s, quan 0.25/s; `spoiled` ở ngưỡng 30 | `test_fresh_p3.test_spoiled_at_threshold_on_first_gather_step` | PASS |
| Giữ chỗ theo id; giá `floor(giá × avg fresh/100)` | cook_started trong test quán | PASS |
| Bàn giao file + day | smoke + `test_day_p2` | PASS |
| Suite | `unittest discover` | PASS |
