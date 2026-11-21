"""Benchmark (TICKET-04 mục 1): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (độ tươi, cá bơi/sinh, Cá Sấu Năm Chèo, dòng lũ nếu khai mở rộng), Út Sen đứng
yên ở bến, seed cố định. Làm nóng 3 s rồi đo `--duration` giây.

Một "khung" = đúng phần việc cửa sổ chơi làm ở phía Python cho mỗi khung hình: bước sim 1 tick, dựng
snapshot (như GET /state) và mã hóa JSON. Cảnh hết giờ thì dựng lại để mọi khung đều có việc thật.
GIỚI HẠN: phần vẽ canvas chạy trong trình duyệt nên không đo được bằng thư viện chuẩn Python; số này
là trần FPS phía mô phỏng + truyền snapshot, không phải FPS GPU.

bench.json: {avg_fps, p1_low_fps, frames, measured_s, load_ms}
  avg_fps = frames / measured_s
  p1_low_fps = 1 / trung bình thời gian của max(1, ceil(0.01 × frames)) khung chậm nhất (giây)
  load_ms = mili giây từ lúc khởi chạy lệnh đến khung đầu tiên của cảnh đo
"""

import argparse
import json
import math
import sys
import time

_T_LAUNCH = time.perf_counter()


def _scene(tuning, seed):
    from .ids import IdAllocator
    from .rng import Streams
    from .sim.gather import GatherSim

    scenario = {"player": {"pos": list(tuning["gather"]["start_pos"])}}
    return GatherSim(tuning, scenario, Streams(seed), IdAllocator(), day=1)


def _frame(state, tuning, seed, idle):
    from .jsonl import dumps

    if state["sim"].done:
        state["sim"] = _scene(tuning, seed)
    state["sim"].step(idle)
    dumps(state["sim"].snapshot())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", type=float, default=3.0, help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("--duration phải > 0\n")
        return 2

    from .contract import load_contract
    from .inputs import InputState

    tuning = load_contract()["tuning"]
    idle = InputState((0.0, 0.0), {}, set())
    state = {"sim": _scene(tuning, a.seed)}
    _frame(state, tuning, a.seed, idle)  # khung đầu tiên của cảnh đo
    load_ms = int(round((time.perf_counter() - _T_LAUNCH) * 1000))

    warm_end = time.perf_counter() + a.warmup
    while time.perf_counter() < warm_end:
        _frame(state, tuning, a.seed, idle)

    dts = []
    start = time.perf_counter()
    deadline = start + a.duration
    while True:
        f0 = time.perf_counter()
        if f0 >= deadline:
            break
        _frame(state, tuning, a.seed, idle)
        dts.append(time.perf_counter() - f0)
    measured_s = time.perf_counter() - start
    frames = len(dts)
    n_low = max(1, math.ceil(0.01 * frames))
    slow = sorted(dts, reverse=True)[:n_low]
    out = {
        "avg_fps": frames / measured_s if measured_s > 0 else 0.0,
        "p1_low_fps": (len(slow) / sum(slow)) if slow and sum(slow) > 0 else 0.0,
        "frames": frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
