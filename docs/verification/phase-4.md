# Ma trận truy vết Phase 4 — TICKET-04 "Phát hành v1.0.0" (Test Contract v1.3)

**Commit bàn giao (tag `phase-4` = GitHub Release `v1.0.0`):** ghi ở `docs/proof/phase-4/tags.log`. Bộ test và bằng chứng `docs/proof/phase-{2,3,4}/` được tạo lại trên chính commit đó bằng `python3 tools/make_proof.py`; kết quả suite ở `docs/proof/phase-4/test-suite.log`.

| AC | Yêu cầu | Kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | `contract_version:"1.3"`, `bench_cmd`, `soak_cmd` ở gốc manifest | `test_contract_and_cli` | `game.contract.json` | ĐẠT |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` tạo đủ 5 trường, đúng công thức | `test_bench_p4` | `docs/proof/phase-4/bench.{json,log}` | ĐẠT — mốc avg ≥ 60 / 1% low ≥ 30 / load ≤ 10 s đạt **phía Python**; **không** đo vẽ canvas (giới hạn ghi trong README) |
| AC-P4-03 | `soak_cmd --seed 7 --days 10`: `days_completed = days`, `crashes = 0`, `results[]` lúc Shop đóng, lặp lại giống nhau | `test_soak_p4` (4 test) | `docs/proof/phase-4/soak.{json,log}` | ĐẠT |
| AC-P4-04 | Cảnh báo chữ/biểu tượng: thủy quái gần, oxy sắp hết, khách sắp giận; chế độ tương phản cao | Đọc code + chạy cửa sổ chơi | `index.html`: "🐊 Thủy quái!" + viền tím, "Sắp hết oxy"/"🫧 Hết hơi!", "⚠ sắp giận", phím **H** | ĐẠT phần code — **chưa có** ảnh/ghi hình chơi thử cả 3 cảnh báo ở chế độ H (việc của Nhài) |
| AC-P4-05 | Clone sạch chạy bản có giao diện trong ≤ 3 lệnh; README ghi môi trường, điều khiển, test, headless, bench | Clone vào thư mục trống, chạy 3 lệnh | `docs/proof/phase-4/clean-clone.log` | ĐẠT trên Windows (lệnh tương đương); **cần chạy lại trên macOS/Linux** |
| AC-P4-06 | Regression P1–P3 còn hiệu lực | `unittest discover` | `docs/proof/phase-4/test-suite.log` | ĐẠT |
| AC-P4-07 | CHANGELOG theo phase, release notes, bản đóng gói, CREDITS/LICENSE | Rà file | `CHANGELOG.md`, `docs/release-notes-v1.0.0.md`, `chonoi-doctorx-v1.0.0.zip` (đính kèm Release), `LICENSE`, `CREDITS.md` | ĐẠT một phần — 11 asset chưa ghi nguồn (liệt kê trong CREDITS) |
| AC-P4-08 | Tag `phase-4` và Release `v1.0.0` cùng trỏ một commit trên `main` | `git ls-remote --tags` | `docs/proof/phase-4/tags.log` | Xem log (Release cần công bố trên GitHub) |
| AC-P4-09 | Retro rà hành động P2, phản tư đủ người | `docs/retro.md`, `docs/members/*.md` | — | ĐẠT một phần — retro là bản nháp tổng hợp của Diệp; phản tư của 5 bạn còn lại cần tự viết |
| AC-P4-10 | Mở rộng `leaderboard` (khai `extensions`, top 10, hòa giữ thứ tự ghi, cặp cờ, mã 2, không đổi JSONL) | `test_ext_leaderboard` (8 test) | `docs/proof/phase-4/leaderboard.{log,export.json}` | ĐẠT |
| AC-P4-11 | Phụ đề SFX cho âm thanh đã có, kiểm khi tắt tiếng | Code `sfxSubtitle` | — | ĐẠT phần code — chưa có ghi hình chơi thử khi tắt tiếng |

## Đánh giá ngắn
- Đạt: lệnh v1.3, bench/soak đúng cấu trúc (đã viết lại vì bản cũ đo sai), clone sạch, regression, leaderboard.
- Giới hạn trung thực: bench không đo GPU; chưa có ảnh chơi thử; clone sạch mới thử trên Windows; một phần asset chưa rõ nguồn.
