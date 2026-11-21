# Kiểm chứng QA Phase 4 · KhangMai123

Mã kiểm chứng `5ee206c` (`phase-4`, `v1.0.0`), Test Contract v1.3, Windows, Python 3.13.18. Đối chiếu [ma trận Phase 4](../../verification/phase-4.md) cho AC-P4-02, AC-P4-03 và AC-P4-06. Smoke Day và bàn giao kho đối chiếu thêm AC-P2-06 và AC-P3-03.

| Phép kiểm | Kết quả |
|---|---|
| Regression P1–P4 | **157/157 đạt**, 0 FAIL, 0 ERROR (25,177 giây). `tools/check_team.py` xác nhận đủ 6 thành viên. |
| Một Ngày, seed 1 | Mã thoát 0. Thứ tự pha `gather`, `quan`, `shop`. Tick 22.200 kết thúc với `days_complete`, hoàn thành 1 Ngày (0,487 giây). |
| Kho cá thể, seed 42 | Cả hai tiến trình thoát 0. `gather_end` là `docked`; `I1/ca_linh` khớp giữa event, file kho và kho Quán tick 0. Độ tươi lần lượt là 99,992 / 99,99166666666666 / 99,992, trong dung sai ±0,01. Kho đếm v1.0 trả mã 2. |
| Soak, seed 7 | Hai lượt đều thoát 0, hoàn thành 10/10 Ngày, 0 crash. Sau khi bỏ `duration_s`, hai JSON giống nhau. Ngày 1–10 đều có `earned=0`, `reputation=3.0`, `score=300`. |
| Benchmark Python, seed 42 | 275.422 khung trong 30,0002393 giây. Trung bình 9.180,66 FPS, 1% low 3.702,48 FPS, tải 24 ms. JSON đủ 5 trường và `avg_fps = frames / measured_s`. |

Benchmark đo bước mô phỏng, dựng snapshot và mã hóa JSON phía Python. AC-P4-02 vẫn thiếu phép đo render canvas ở 1280 × 720 theo TICKET-04. Soak dùng bot cập bến ngay và đóng Shop ở bước đầu, nên phép đo chỉ kiểm được sự ổn định và lặp lại của vòng Ngày. Suite có test riêng cho pause, mua nâng cấp và độ tươi.

## Lệnh tái lập

Chạy tại gốc repo, dùng Python của `.venv` và `python3.exe` của cùng môi trường trên PATH để các test gọi được `headless_cmd`. Đặt các file đầu ra trong thư mục tạm.

```powershell
$env:Path = (Resolve-Path .venv/Scripts).Path + ';' + $env:Path
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
$qaOut = Join-Path ([IO.Path]::GetTempPath()) ('doctorx-qa-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $qaOut
python -m unittest discover -s tests -q
python tools/check_team.py
python -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --out "$qaOut/day.jsonl"
python -m chonoi.soak --seed 7 --days 10 --out "$qaOut/soak.json"
python -m chonoi.soak --seed 7 --days 10 --out "$qaOut/soak-repeat.json"
python -m chonoi.bench --seed 42 --duration 30 --out "$qaOut/bench.json"
```

Tạo `dock.json`, `dock-inputs.json` và `old.json` trong `$qaOut` theo thứ tự với nội dung sau.

```jsonl
{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}
{"frames":[{"tick":0,"interact":true}]}
{"items":{"ca_linh":1}}
```

```powershell
python -m chonoi.headless --mode gather --seed 42 --scenario "$qaOut/dock.json" --inputs "$qaOut/dock-inputs.json" --ticks 1 --out "$qaOut/gather.jsonl" --inventory-out "$qaOut/catch.json"
python -m chonoi.headless --mode quan --seed 42 --inventory "$qaOut/catch.json" --ticks 0 --out "$qaOut/quan.jsonl"
python -m chonoi.headless --mode quan --seed 42 --inventory "$qaOut/old.json" --ticks 0 --out "$qaOut/old.jsonl"
```

So `gather_end.data.inventory.items` và `stock` của snapshot Quán tick 0 với `items` trong `catch.json`. So chính xác `id` và `kind`, dùng dung sai ±0,01 cho `fresh`. So hai file soak sau khi bỏ `duration_s`.
