# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh — Quán Ăn Chợ Nổi v1.0.0 (nhóm DoctorX)

**Yêu cầu môi trường:** Python **3.10+** (CI và nhóm dùng 3.12), chỉ thư viện chuẩn — không cần `pip install`. Git để clone. Trình duyệt hiện đại (Chrome/Firefox/Safari/Edge) để chơi; màn hình chuẩn 1280×720.

**Từ clone sạch, 3 lệnh (macOS / Linux):**

```bash
git clone https://github.com/KhangMai123/K5-L3B-LAB-Day12-AI-SDLC-DoctorX.git && cd K5-L3B-LAB-Day12-AI-SDLC-DoctorX
PYTHONPATH=tests:. python3 -m unittest discover -s tests      # (tùy chọn) bộ test
python3 -m chonoi.live --mode day --days 5                     # chơi: mở địa chỉ in ra (mặc định http://127.0.0.1:8000/)
```

Bản đóng gói ở GitHub Release `v1.0.0` (`chonoi-doctorx-v1.0.0.zip`): giải nén, `cd` vào thư mục rồi chạy lệnh thứ 3.
Windows: dùng `python` thay `python3`, và `PYTHONPATH=tests;.` (xem `AGENTS.md` nếu smoke test cần lệnh `python3`).

### Điều khiển

| Cảnh | Phím |
|---|---|
| Lặn & Hái | **WASD / mũi tên** bơi · **E** hái (ở mặt nước) / cập bến · **Space** bắt cá (dưới nước) |
| Mở Quán | **WASD / mũi tên** đi · **E** nấu ở bếp / bưng món / dọn cho khách (đối tượng gần nhất) |
| Shop | **1** mua Bình oxy · **2** mua Áo phao · **3** mua Vợt hút cá · **E / Enter** đóng Shop |
| Mọi lúc | **Esc / P** tạm dừng · **H** tương phản cao · **M** bật/tắt Má Tư · **L** nhật ký event · **R** chơi lại |

Cảnh báo dễ nhận biết (có chữ + biểu tượng, thử được ở chế độ tương phản cao **H**): "Sắp hết oxy" khi oxy < 25 % và "🫧 Hết hơi!" khi oxy cạn, "🐊 Thủy quái! Tránh xa!" + viền tím nhấp nháy khi Cá Sấu trong 10 m, "⚠ sắp giận" ở bàn khi kiên nhẫn < 25 %, 🌊 báo trước dòng lũ (kèm âm thanh và phụ đề).

### Lệnh cho máy chấm / kiểm chứng

| Việc | Lệnh |
|---|---|
| Test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` |
| Headless | `python3 -m chonoi.headless --mode gather\|quan\|day --seed 1 --ticks 600 --out out.jsonl [--days N] [--scenario f] [--inputs f] [--inventory f] [--inventory-out f]` |
| Một Ngày | `python3 -m chonoi.headless --mode day --seed 1 --days 1 --ticks 22200 --out day.jsonl` |
| Benchmark | `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` |
| Soak | `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` |
| Xếp hạng | `python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 120000 --out d.jsonl --leaderboard store.json --player-name "Út Sen"` rồi `python3 -m chonoi.live --mode gather --export-leaderboard out.json --leaderboard store.json` |
| Tạo lại bằng chứng | `python3 tools/make_proof.py` → `docs/proof/phase-{2,3,4}/` |

Điểm = `earned + 100 × floor(reputation)`; tiền tính theo nghìn đồng. File kho v1.2 là mảng cá thể `{"items":[{"id","kind","fresh"}]}` — xem [hợp đồng](docs/contracts/README.md) và [file mẫu](docs/contracts/inventory.sample.json).

### Giới hạn đã biết

- `bench` đo phía Python của mỗi khung (bước sim + snapshot + JSON như `GET /state`); phần vẽ canvas chạy trong trình duyệt nên **không** đo FPS GPU. Số liệu: `docs/proof/phase-4/bench.json`.
- Cửa sổ chơi là bản canvas 2D chạy trong trình duyệt qua server cục bộ, không phải ứng dụng cài đặt.
- Bảng xếp hạng chỉ ghi qua headless `--mode day --days 5` (cặp `--leaderboard` + `--player-name`); cửa sổ chơi chưa có ô nhập tên.
- Mở rộng **Khách đặt trước** (`reservations`), Lao xua, Rắn Hổ Mây, Chợ Chú Sáu, Sổ tay & Cá Hô, Settings âm lượng: **chưa làm**.
- Asset nhân vật quán Phase 2 còn thiếu ghi nguồn/giấy phép chi tiết, xem `CREDITS.md`.


## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Sáng tạo của nhóm

### Mở rộng đã làm (khai trong `extensions` của `game.contract.json`)

| Mã | Mở rộng (ticket) | Bằng chứng |
|---|---|---|
| `burn` | Cháy món (P2) | `tests/test_quan_p1.py`, `quan.burn_s: 20` |
| `net` | Vợt hút cá: cấp 1 250k/4 m/2 đàn, cấp 2 500k/6 m/3 đàn (P2) | `tests/test_ext_net.py` |
| `current` | Dòng nước lũ: mỗi 1800 tick, báo trước 120 tick (chữ + 🌊 + âm thanh), 480 tick, +1.5 m/s khi d ≥ 10 (P3) | `tests/test_ext_current.py` |
| `leaderboard` | Bảng xếp hạng cục bộ top 10 (P4) | `tests/test_ext_leaderboard.py`, `docs/proof/phase-4/leaderboard.log` |
| — | Phụ đề SFX: mỗi âm thanh đã có (tiếng báo dòng lũ) hiện phụ đề 2.5 s, kể cả khi tắt tiếng (P4) | `chonoi/web/index.html` (`sfxSubtitle`) |

Mọi mở rộng đọc số từ `game.contract.json`; `net` cấp 0 giữ nguyên luật bắt cá lõi; `current` tắt được bằng `gather.random_current:false`; bảng xếp hạng không đổi JSONL (có test so từng byte).

### Chi tiết: Cháy món (`burn`)
- Khai `extensions: ["burn"]`, `quan.burn_s: 20`. Món ready quá 1200 tick bị cháy (`dish_burnt`), nguyên liệu mất, thử giữ lại đơn.
- Chỉ ảnh hưởng quán khi mở rộng bật; số liệu từ `game.contract.json`.

### Sáng tạo: Lời Má Tư (Nhài, `client/ui`)
Má Tư hiện ở góc dưới bên trái cửa sổ chơi và nói giọng Nam Bộ theo diễn biến:
- **Mở đầu mỗi buổi:** dặn Út Sen lặn, hoặc giục mở quán.
- **Buổi sáng:** phản ứng khi hết hơi, ngạt, ngất, giỏ đầy, hái bông điên điển hay bông súng, bắt được cá linh hay cá lóc, cập bến.
- **Buổi tối:** phản ứng khi khách tới, không còn món, món chín, được boa, khách bỏ về, hết ca.

Khi nhiều sự kiện xảy ra cùng lúc, chuyện gấp (ngạt, ngất, khách bỏ về) được nói trước. Phím **M** bật hoặc tắt Má Tư.

Mở rộng này **không ảnh hưởng lõi**:
- Code chỉ nằm trong `chonoi/web/index.html` và chỉ đọc snapshot từ `/state`, không gửi gì vào sim. Câu thoại chọn theo tick, không dùng RNG của sim. Headless không tải file này.
- **Bằng chứng:** output headless (`gather` có inputs và `quan`, seed 7, 600 tick) của nhánh có mở rộng giống từng byte với `main` trước khi có mở rộng, xem [`docs/proof/phase-1/mo-rong-1-headless.txt`](docs/proof/phase-1/mo-rong-1-headless.txt). Bộ test vẫn xanh hết.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
