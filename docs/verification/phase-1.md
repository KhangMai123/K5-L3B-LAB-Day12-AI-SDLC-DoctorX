# Ma trận truy vết Phase 1 — DoctorX (QA Lead: KhangMai123)

Chuẩn đối chiếu là PRD-0 Test Contract v1.0. Bộ kiểm thử tích hợp trên Windows, Python 3.13.18, đạt **110/110**, với 0 FAIL và 0 ERROR. [Kết quả chạy đầy đủ](../proof/phase-1/test-suite.log).

| AC / Yêu cầu | Kiểm chứng | Kết quả | Bằng chứng |
|---|---|---|---|
| A. Phiên bản và tuning | `test_contract_and_cli.ContractValidation` | PASS | [Bộ test](../proof/phase-1/test-suite.log) |
| B. CLI và mã thoát 0/1/2 | `test_contract_and_cli.CliFlagsAndExitCodes`, `test_smoke_p1.Contract` | PASS | [Bộ test](../proof/phase-1/test-suite.log) |
| C. Input, cạnh nút, giới hạn vector di chuyển | `test_scenario_and_inputs.InputsContract`, `test_python_starter_units.Units` | PASS | [Bộ test](../proof/phase-1/test-suite.log) |
| D. Fixture, thứ tự id, liên kết món và dữ liệu mâu thuẫn | `test_scenario_and_inputs.ScenarioContract`, `test_smoke_p1.ScenarioModes`, `test_quan_lat4` | PASS | [Bộ test](../proof/phase-1/test-suite.log) |
| E. JSONL, snapshot, thứ tự event, làm tròn và điểm | `test_jsonl_and_determinism.JsonlAndDeterminism`, `test_smoke_p1.Contract` | PASS | [Bộ test](../proof/phase-1/test-suite.log) |
| E. Determinism của hai pha và file kho | Test lặp seed và smoke hai tiến trình độc lập, chạy lại cùng dữ liệu | PASS, JSONL của cả hai pha và `catch.json` giống từng byte | [Bộ test](../proof/phase-1/test-suite.log), [Smoke kho](../proof/phase-1/smoke-two-process.log) |
| F. Gather Lát 1, di chuyển, oxy, ngạt và ngất | `test_smoke_p1.Movement`, `test_gather_lat1`, `test_gather_p1.GatherLat1OxygenChokeFaint` | PASS, ngạt lần đầu tại t+59 và bỏ giỏ LIFO | [Bộ test](../proof/phase-1/test-suite.log) |
| E–F. Gather Lát 2, hái, tái sinh, bắt, hồi chiêu, giỏ đầy và ưu tiên bến | `test_gather_lat2`, `test_gather_p1.GatherLat2NodesCatchDock` | PASS, `hold_full` ghi rõ hành động, id đích, số ô cần và số ô trống | [Bộ test](../proof/phase-1/test-suite.log) |
| E–F. Quán Lát 3, lịch khách, kho khả dụng và giữ chỗ | `test_quan_p1.QuanLat3CustomersAndReservation`, `test_python_starter_units.Units` | PASS, `customer_arrived` và `customer_left` dùng `order_id`, `no_dish` phát `{}` | [Bộ test](../proof/phase-1/test-suite.log) |
| D–F. Quán Lát 4, nấu, bưng, phục vụ, tính boa và thu tiền | `test_quan_p1.QuanLat4CookServePayClose`, `test_quan_lat4` | PASS, hòa `order_tick` xét id bàn, payload món có giá, phục vụ hợp lệ ở tick kiên nhẫn về 0 | [Bộ test](../proof/phase-1/test-suite.log) |
| F. Quán đóng ca | `test_closing_pays_eating_just_served_clears_stoves_and_no_spawn` | PASS, thu tiền cả khách vừa được phục vụ, khách chờ rời không mất uy tín, dọn bếp/tay và không sinh khách ở tick cuối | [Bộ test](../proof/phase-1/test-suite.log) |
| G. Schema kho và chuyển kho giữa hai tiến trình | `test_inventory_and_smoke`, `test_smoke_p1.Integration`, `test_gather_lat2_inventory`, smoke PRD-0 mục G | PASS, cả hai tiến trình thoát 0, `stock` tick 0 đúng `{"bong_sung":2,"ca_loc":1}` | [Smoke kho](../proof/phase-1/smoke-two-process.log), [Bộ test](../proof/phase-1/test-suite.log) |
| DoD. Danh sách thành viên | `python tools/check_team.py` | PASS, 6/6 handle và `team_size` khớp | [Kiểm danh sách](../proof/phase-1/check-team.log) |
| DoD. HUD hai buổi và Mở rộng #1 | `test_live`, ảnh HUD của Nhài, tái lập hash trước/sau mở rộng và so headless ở bản tích hợp có/không có thư mục web | PASS cho live API và so sánh từng byte. Ảnh HUD tham chiếu các commit ghi trong bằng chứng UI | [HUD](../proof/phase-1/ui/README.md), [Bằng chứng gốc](../proof/phase-1/mo-rong-1-headless.txt), [Đối chiếu headless](../proof/phase-1/headless-ui-isolation.log) |
| DoD. Hướng dẫn clean clone, điều khiển, công thức điểm và kho | Đối chiếu `README.md` với PRD-0 mục 7 | Đủ mục. Lệnh kiểm thử được xác minh trên Windows, chưa chạy trên macOS/Linux | [README](../../README.md), [Schema kho](../contracts/README.md) |

Các bằng chứng trên áp dụng cho bản tích hợp trước review. Integrator kiểm chứng lại bản bàn giao trước khi gắn tag `phase-1` trên `main`.
