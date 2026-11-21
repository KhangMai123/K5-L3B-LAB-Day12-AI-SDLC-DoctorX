# Ma trận truy vết Phase 1 — DoctorX (QA Lead: KhangMai123)

> Kiểm chứng trên nhánh `p1/qa-khang` (tách từ `main` commit `5693817`). Chỉ ghi kết quả chạy thực tế; các phần thuộc lát 1–4 chưa merge vào `main` được ghi trung thực `FAIL` / `BLOCKED` theo owner.

| AC / Yêu cầu | Lệnh / Test kiểm chứng | Actual | Kết quả | Bằng chứng (`docs/proof/phase-1/...`) | Owner |
|---|---|---|---|---|---|
| Contract v1.0 & tuning (`game.contract.json`, `chonoi/contract.py`) | `test_contract_and_cli.ContractValidation` | 2/2 test PASS | PASS | `test-suite.log` | Khang (`qa`) / Diệp (`Integrator`) |
| CLI headless & exit code `0/1/2` (`--ticks 0`, flags sai pha, trùng đường dẫn, lỗi ghi) | `test_contract_and_cli.CliFlagsAndExitCodes`, `test_smoke_p1.Contract` | 10/10 test PASS | PASS | `test-suite.log` | Khang (`qa`) |
| Inputs (`frames`, cạnh lên `false->true`, normalize `move`, thiếu file) | `test_scenario_and_inputs.InputsContract`, `test_python_starter_units.Units` | PASS toàn bộ | PASS | `test-suite.log` | Khang (`qa`) |
| Scenario & kiểm mâu thuẫn (`chonoi/scenario.py`, thay mảng `[]`, sort `F2/F10`, mâu thuẫn -> 2) | `test_scenario_and_inputs.ScenarioContract`, `test_smoke_p1.ScenarioModes` | 7/7 test PASS | PASS | `test-suite.log` | Khang (`qa`) |
| JSONL schema, cadence, thứ tự event trước snapshot, làm tròn 3 chữ số, `score` | `test_jsonl_and_determinism.JsonlAndDeterminism` (3 test) | 3/3 test PASS | PASS | `test-suite.log` | Khang (`qa`) |
| Determinism byte-for-byte (`gather` & `quan`) | `test_con_02_deterministic_bytes`, `test_quan_determinism_byte_for_byte` | 2/2 test PASS | PASS | `test-suite.log` | Khang (`qa`) |
| Contract file kho & Smoke test 2 tiến trình (`gather` -> `catch.json` -> `quan`) | `test_inventory_and_smoke.InventoryContractAndSmoke`, `test_smoke_p1.Integration` | 9/9 test PASS; `gather_exit=0`, `quan_exit=0`, `catch.json={"items":{"bong_sung":2,"ca_loc":1}}` | PASS | `smoke-two-process.log`, `test-suite.log` | Khang (`qa`) / Phát / Diệp |
| Gather — bơi, ramp, biên, hết giờ giữ giỏ, ưu tiên bến | `test_smoke_p1.Movement`, `test_dock_has_priority_over_node_even_at_exact_boundary` | 7/7 test PASS | PASS | `test-suite.log` | Hưng (Lát 1) / Phát (Lát 2) |
| Gather Lát 1 — `dive`/`surface`, oxy, `oxygen_empty`, `choke` (t+59), `faint` LIFO & kho rỗng | `test_gather_p1.GatherLat1OxygenChokeFaint` | 0/4 PASS (4 FAIL — `sim/gather.py` trên `main` còn `TODO(nhóm, lát 1)`) | FAIL (chờ merge Lát 1) | `test-suite.log` | Hưng (`sim/gather` — Lát 1) |
| Gather Lát 2 — hái mặt nước, `node_regrown`, `catch` dưới nước, cooldown, `hold_full` | `test_gather_p1.GatherLat2NodesCatchDock` (trừ test bến) | 0/2 PASS (2 FAIL — `sim/gather.py` trên `main` còn `TODO(nhóm, lát 2)`) | FAIL (chờ merge Lát 2) | `test-suite.log` | Phát (`sim/gather` — Lát 2) |
| Quán Lát 3 — `customer_arrived`, chọn món & giữ chỗ, `no_dish`, kiên nhẫn, `customer_left` | `test_quan_p1.QuanLat3CustomersAndReservation` | 0/3 PASS (3 FAIL — `sim/quan.py` trên `main` còn `TODO(nhóm, lát 3)`) | FAIL (chờ merge Lát 3) | `test-suite.log` | Minh (`sim/quan` — Lát 3) |
| Quán Lát 4 — `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, tip, closing, `quan_end` | `test_quan_p1.QuanLat4CookServePayClose` | 0/2 PASS (2 FAIL — `sim/quan.py` trên `main` còn `TODO(nhóm, lát 4)`) | FAIL (chờ merge Lát 4) | `test-suite.log` | Diệp (`sim/quan` — Lát 4) |
| Kiểm danh sách thành viên (`tools/check_team.py`) | `python tools/check_team.py` | Exit 1: thành viên #1 (Hưng), #2 (Phát), #3 (Minh) còn `…` trên `main`; `KhangMai123` (#6) đã hợp lệ | BLOCKED | `check-team.log` | Hưng, Phát, Minh |
| UI/HUD chơi thử trên trình duyệt, `run_cmd` | Chưa chạy kiểm thử trình duyệt thủ công ở phiên headless Windows | Chưa kiểm tra trực quan | NOT_RUN | — | Nhài (`client/ui`) |
| 3 lệnh clean clone trên macOS/Linux & tag `phase-1` trên `main` | Kiểm tra từ môi trường Windows; chưa có quyền/chỉ định tag `main` | Chưa chạy trên macOS/Linux; tag `phase-1` do Integrator gắn sau khi gộp các lát | NOT_RUN / BLOCKED | — | Diệp (`Integrator`) |

## Đánh giá ngắn
- **Yêu cầu đạt:** Toàn bộ phần khung Contract v1.0, CLI exit code `0/1/2`, kiểm validation `contract.py` và `scenario.py`, JSONL schema/determinism, contract file kho và smoke test 2 tiến trình (`gather` -> `catch.json` -> `quan`) đều PASS (54/65 test).
- **Yêu cầu chưa đạt / phụ thuộc đồng đội:**
  - 11/65 test (`test_gather_p1.py` 6 test, `test_quan_p1.py` 5 test) đang FAIL trên `main` vì code Lát 1–4 (`chonoi/sim/gather.py`, `chonoi/sim/quan.py`) đang nằm ở các nhánh riêng hoặc chưa hoàn tất/merge vào `main`.
  - `tools/check_team.py` còn báo thiếu GitHub handle của Hưng (#1), Phát (#2), Minh (#3) trên `main`.
  - Nhóm 6 người cần hoàn thành tối thiểu 2 mục mở rộng trong cả buổi lab (theo PRD-0); QA chưa làm mở rộng #2 ở lượt này vì ưu tiên ổn định bộ test lõi Phase 1.
- **Điều cần chỉnh cho bước tiếp theo:** Integrator (Diệp) tổng hợp/merge các nhánh Lát 1–4 vào `main`, các thành viên điền đủ handle vào `TEAM.md`, chạy lại `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` cho xanh 65/65 trước khi gắn tag `phase-1`.
