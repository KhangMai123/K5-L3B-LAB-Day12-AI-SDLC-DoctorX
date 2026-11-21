# Changelog — Quán Ăn Chợ Nổi (nhóm DoctorX)

Định dạng: mỗi phase một mục, mới nhất ở trên. Tag tương ứng: `phase-1` … `phase-4`, Release `v1.0.0`.

## v1.0.0 — Phase 4 (Test Contract v1.3)

### Thêm
- `bench_cmd` (`python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json`): làm nóng 3 s, đo 30 s; mỗi khung = bước sim + snapshot + JSON; xuất `avg_fps, p1_low_fps, frames, measured_s, load_ms`.
- `soak_cmd` (`python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`): **một** DaySim chạy liền N Ngày, kế hoạch D1–D5 lặp, tiền/uy tín/cấp/id cá thể nối tiếp; bot tất định.
- Mở rộng `leaderboard`: top 10 cục bộ; headless day `--leaderboard` + `--player-name`; `run_cmd --export-leaderboard`.
- Phụ đề SFX cho âm thanh đã có (tiếng báo dòng lũ).
- Cảnh báo: "🫧 Hết hơi!", "🐊 Thủy quái!" + viền tím, "⚠ sắp giận"; tương phản cao (phím H).
- `tools/make_proof.py` tạo lại bằng chứng P2–P4; `LICENSE`.

### Sửa
- `bench`: trước đây sau khi buổi sáng kết thúc thì đo vòng rỗng → FPS bị thổi phồng.
- `soak`: trước đây mỗi Ngày một Session `days=1` (Ngày nào cũng là Ngày 1, ca chỉ 30 tick).

### Đổi manifest
- `contract_version: "1.3"`, thêm `bench_cmd`, `soak_cmd`; `extensions: ["burn", "net", "current", "leaderboard"]`.

## Phase 3 (Test Contract v1.2) — **BREAKING**

### Breaking change: kho đếm → kho cá thể
- File kho, `gather_end.data.inventory`, snapshot `hold`/`stock` đổi từ object đếm `{"items":{"ca_loc":1}}` sang mảng cá thể `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`.
- File kho đếm v1.0 → **mã 2**. `customers[].reserved` là mảng id cá thể. `cook_started.data.items` là mảng cá thể; `lost` trong `monster_hit`/`faint` là mảng cá thể theo LIFO.
- **Cách cập nhật fixture:** `gather.hold` và `quan.stock` viết thành mảng `{id, kind, fresh}` (bỏ `id` thì được cấp `I1, I2…`); kho rỗng `{"items":[]}`; `reserved` của khách là danh sách id có trong `stock`. Mẫu: `docs/contracts/inventory.sample.json`.

### Thêm
- Độ tươi: giỏ −0.5/s, kho quán −0.25/s, `spoiled` một lần khi qua ngưỡng 30; giữ chỗ theo id (tươi nhất, hòa theo id), giữ lại một lần khi hàng vừa ươn; `base_price = floor(giá × trung bình fresh / 100)`.
- Mở rộng `current` (dòng nước lũ): báo trước 120 tick bằng chữ + 🌊 + âm thanh, chảy 480 tick mỗi 1800 tick, +1.5 m/s khi d ≥ 10.
- HUD: thanh độ tươi từng ô giỏ, nhãn "ươn", % tươi thấp nhất ở kho quán.

### Sửa
- Ngày ≥ 2 dùng lại id trong mẫu `gather.hold` (trùng `I1`) → nay cấp id mới theo thứ tự mảng.
- HUD giỏ vỡ (`TypeError`) khi hàng là cá thể.

## Phase 2 (Test Contract v1.1)

### Thêm
- Số chuẩn TICKET-02; 6 nguyên liệu (`ca_keo`, `keo_neo` mới), 6 món; 2 bếp / 4 bàn.
- Cá bơi/sinh theo seed, Cá Sấu Năm Chèo (patrol/chase/recoil, `monster_hit`, bất tử 90 tick).
- `--mode day --days N`: `day_start → day_plan → gather → quan → shop`; Shop nâng cấp `oxygen`/`hp` (áp từ Ngày kế).
- Pause ở cả ba mode (`paused`/`resumed`, `state:"paused"`); UI Esc/P + màn pause.
- Mở rộng `burn` (cháy món) và `net` (vợt hút cá, phím 3 ở Shop).
- HUD "Cần lấy: đã lấy/cần" theo kế hoạch Ngày.

### Sửa
- Lịch khách trả về số chuẩn `120 + 900·k`, bỏ lượt khi đầy bàn (trước đó 60 / 8 s).
- Vỏ event day: event tick 0 đúng thứ tự; event kết thúc mang pha cũ.
- `sim_tick` đứng yên khi pause (trước đó nhảy theo tick ngoài).
- Cá Sấu recoil lùi **xa** người chơi (trước đó lùi về phía người chơi).

## Phase 1 (Test Contract v1.0)
- Lát 1–4 gather/quan lõi (oxy, ngạt, ngất, giỏ; hái, bắt cá, cập bến, ghi kho; khách, giữ chỗ, kiên nhẫn; bếp, bưng, phục vụ, tiền, uy tín).
- Hợp đồng tích hợp `docs/contracts/`; HUD 2 buổi; sáng tạo "Lời Má Tư".
