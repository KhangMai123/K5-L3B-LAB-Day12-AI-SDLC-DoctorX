# Retro nhóm DoctorX

## Phase 1
- Điều tốt: bốn lát + HUD gộp sớm; smoke kho 2 tiến trình xanh; verification 110/110; mở rộng #1 (Má Tư) không đổi headless.
- Điều tệ: Windows thiếu `python3` làm smoke đỏ giả; payload Lát 2 lệch hợp đồng một lần trước khi đồng bộ `docs/contracts/`.
- 1 hành động cho Phase 2: mỗi lần đổi contract/schema phải cập nhật test + fixture cùng commit; chạy smoke `gather --inventory-out` → `quan --inventory` trước khi gộp.

## Phase 2 (không họp kịp — ghi bù khi rà ở Phase 4)
- Điều tốt: cả code day/Shop/cá bơi/Cá Sấu vào `main` trong một lượt (`0a725a8`), suite vẫn xanh.
- Điều tệ: code P2–P4 vào **một commit lớn của một người** nên các lát khác không có phần để nhận; không ai chạy smoke day thật trước khi gộp; tag `phase-1`/`phase-2` không được gắn đúng hạn.
- 1 hành động cho Phase 3–4: mỗi lỗi lệch ticket phải có **test đỏ trước** rồi mới sửa; bằng chứng tạo bằng script chạy thật (`tools/make_proof.py`), không chép tay.

## Phase 4 (cuối) — bản nháp tổng hợp từ bằng chứng trong repo (Diệp soạn, cả nhóm chốt lại)

**Rà hành động đã chốt:**
- Hành động P1 ("đổi schema thì cập nhật test + fixture cùng commit; chạy smoke trước khi gộp"): **làm được một nửa.** `0a725a8` đổi schema kho sang v1.2 cùng test, nhưng `docs/contracts/inventory.sample.json` vẫn là kho đếm v1.0 (bị mã 2) tới tận Phase 4; `921f3a8` đổi số khách 120/15 s → 60/8 s mà không sửa test → 1 test đỏ trên `main`. Lý do: không ai chạy suite trước khi đẩy lúc gấp.
- Hành động P2 ("test đỏ trước rồi sửa; bằng chứng bằng script"): **làm được.** Lỗi vỏ event day, recoil Cá Sấu có test đỏ trên code cũ trước khi sửa; bằng chứng P2–P4 sinh từ `tools/make_proof.py`.

**Điều tốt:** hợp đồng `docs/contracts/` chốt sớm ở P1 giúp lát 3–4 và HUD ghép ngay; UI chỉ đọc snapshot nên sáng tạo (Má Tư, hình ảnh) không phá headless; khi chạy thật để tạo bằng chứng thì lộ ra lỗi mà test không bắt.

**Điều tệ:** lỗi lệch ticket tìm thấy muộn (vỏ event day, pause chỉ có ở day, `sim_tick` nhảy sau pause, recoil ngược hướng, soak chạy 10 lần "Ngày 1", bench đo vòng rỗng, HUD giỏ vỡ với cá thể v1.2); tag các phase trước gắn muộn; một số asset chưa rõ nguồn.

**Số liệu:** commit không tính merge (git shortlog, tới commit bàn giao): Diệp 26+, Nhài 11, Khang 9, Hưng 5, Minh 4, Phát 3 — *số commit không phản ánh khối lượng: `0a725a8` của Hưng là ~2.200 dòng.* 7 PR được merge vào `main`. Đọc code của nhau: review theo cặp dự phòng ở P1; P2–P4 chủ yếu Diệp rà lại `main`. Token theo người: không ai đo được (xem `docs/ai-usage-log.md`).

**Một lần AI sai và cách nhóm xác minh:** AI so độ tươi giữa file kho và JSONL bằng `==` rồi báo bàn giao "KHÔNG ĐẠT". Đọc số thì thấy file giữ `99.99166…` còn JSONL làm tròn `99.992`; ticket cho dung sai ±0.01 → sửa phép so, không sửa luật. Ở P1, AI báo 20 test đỏ, thật ra do Windows không có `python3`; chạy lại với shim thì 32/32 xanh.

**Nếu làm lại, đổi gì:** chia P2–P4 thành PR nhỏ theo lát, mỗi PR phải có suite xanh và smoke day; gắn tag ngay tại mốc giờ; chạy `tools/make_proof.py` từ Phase 2.

**Hành động tiếp theo (có người nhận):**
- Nhài: chơi thử 3 cảnh báo ở chế độ H, lưu ảnh vào `docs/proof/phase-4/ui/`.
- Minh, Hưng, Diệp: bổ sung nguồn cho 11 asset trong `CREDITS.md` hoặc thay bằng hình tự vẽ.
- Phát: chạy lại 3 lệnh README trên macOS/Linux, ghi vào `docs/proof/phase-4/clean-clone.log`.
