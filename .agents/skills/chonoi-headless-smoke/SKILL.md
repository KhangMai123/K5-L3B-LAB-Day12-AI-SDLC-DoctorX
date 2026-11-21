---
name: chonoi-headless-smoke
description: >-
  Chạy smoke headless Chợ Nổi (gather/quan/day) và kiểm file kho hai tiến trình.
  Dùng khi xác minh DoD phase, trước khi gắn tag, hoặc sau khi sửa sim/contract.
---

# Smoke headless Chợ Nổi

## Khi nào dùng
- Sau khi sửa `chonoi/sim/*`, `game.contract.json`, hoặc schema kho.
- Trước tag `phase-n` hoặc bàn giao PR.

## Lệnh (Windows)
```powershell
$env:PYTHONPATH="tests;."
python -m unittest discover -s tests -v
python tools/check_team.py
```

## Smoke kho hai tiến trình (P1+)
Tạo `dock.json` / `dock-inputs.json` theo PRD mục G, rồi:

```powershell
python -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Snapshot quán tick 0 phải khớp `items` trong `catch.json`.

## P2+
Thêm: `python -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --out day.jsonl`

## Lưu ý
- Không dùng `random` / đồng hồ hệ thống trong sim.
- Mã thoát: 0 OK, 2 đầu vào sai, 1 lỗi ghi/chạy.
- Lưu log vào `docs/proof/phase-n/` và dẫn từ `docs/verification/phase-n.md`.
