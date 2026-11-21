# Ma trận truy vết Phase 4 — DoctorX

Contract v1.3 — bench / soak / cảnh báo / phát hành.

| AC | Kiểm chứng | Kết quả |
|---|---|---|
| `contract_version: "1.3"`, `bench_cmd`, `soak_cmd` | `test_contract_and_cli` | PASS |
| `bench_cmd` tạo `bench.json` đủ 5 trường | chạy tay / `docs/proof/phase-4/` | (chạy khi gắn tag) |
| `soak_cmd` 10 Ngày, crashes=0 | chạy tay | (chạy khi gắn tag) |
| Cảnh báo oxy / thủy quái / khách sắp giận + phím H tương phản cao | UI `chonoi/web/index.html` | PASS (code) |
| Regression P1–P3 | `unittest discover` | PASS |
| CHANGELOG / README ≤3 lệnh | README.md | PASS |
