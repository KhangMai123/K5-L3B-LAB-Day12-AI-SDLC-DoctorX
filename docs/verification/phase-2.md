# Ma trận truy vết Phase 2 — DoctorX

Contract v1.1 (sau đó nâng tiếp lên v1.2 trong Phase 3). Kiểm trên Windows.

| AC | Kiểm chứng | Kết quả |
|---|---|---|
| Manifest v1.1: số chuẩn, 6 món, B2/T2–T4, day_plan, shop, monsters | `test_contract_and_cli` | PASS |
| Cá bơi/sinh, Cá Sấu Ngày 1 | `test_day_p2`, snapshot gather | PASS |
| `--mode day` gather→quan→shop | `test_day_p2.test_day_dock_then_shop_done_completes_one_day` | PASS |
| Mở rộng burn | `extensions: ["burn"]`, `quan.burn_s: 20` | PASS (khai báo) |
| Regression P1 | `unittest discover` | PASS |
