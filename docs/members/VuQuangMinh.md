# VuQuangMinh — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Hoàn thiện Lát 3 trong `chonoi/sim/quan.py`: khách fixture, suy `reserved`, lịch khách theo `first_customer_tick` và `customer_interval_s`, chọn bàn trống id nhỏ nhất, chọn món đều theo seed trong món đủ kho khả dụng.
  - Thêm vòng đời khách: `customer_arrived`, `no_dish`, giảm kiên nhẫn từ bước sau, `customer_left` vì patience hoặc closing, và giải phóng `reserved`.
  - Bổ sung kiểm fixture quán trong `chonoi/scenario.py`; đồng bộ tên trạng thái khách theo PRD mục D.
  - Bổ sung hai test lớp 3 trong `tests/test_python_starter_units.py`; kết quả hiện tại là 34/34 test xanh.
- Tôi đã review (kèm link):
  - Đối chiếu `quan.customers[]` với mục D: `order_status`, `reserved`, `patience_ticks_left`, `eat_ticks_left`, `order_tick`, `base_price`, `tip`.
  - Thông báo cho Minh và Diệp cách HUD đọc `hand.order_id` và `stoves[].dish`; đồng bộ `hand` thành `{order_id,dish_id,base_price}`.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Bản đầu chưa bám đầy đủ schema PRD và nhầm cách thể hiện kho: `stock` là kho vật lý, trong khi HUD cần tồn khả dụng sau khi trừ giữ chỗ. Tôi bổ sung `_available_stock()`.
  - AI ban đầu ghi thiếu dấu ngoặc ở biểu thức kiên nhẫn; compile/test phát hiện `SyntaxError` trước khi chạy suite.
- Điều tôi học được:
  - Phải tách rõ kho vật lý, kho khả dụng và món giữ chỗ; tên trường, tick đến và thứ tự giảm kiên nhẫn cần chốt với lát 4/HUD ngay từ đầu.