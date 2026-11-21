"""Benchmark có render: python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json"""

import argparse
import json
import sys
import time


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    t0 = time.perf_counter()
    # Khởi tạo sim gather chuẩn (đứng yên ở bến) — phần "load"
    from .contract import load_contract
    from .ids import IdAllocator
    from .inputs import InputState
    from .rng import Streams
    from .sim.gather import GatherSim

    tuning = load_contract()["tuning"]
    scenario = {
        "player": {"pos": list(tuning["gather"]["start_pos"])},
        "random_fish": True,
    }
    sim = GatherSim(tuning, scenario, Streams(a.seed), IdAllocator(), day=1)
    load_ms = int(round((time.perf_counter() - t0) * 1000))

    idle = InputState((0.0, 0.0), {}, set())
    # warmup 3s
    warm_frames = 0
    warm_end = time.perf_counter() + 3.0
    while time.perf_counter() < warm_end:
        if not sim.done:
            sim.step(idle)
        warm_frames += 1

    # measure
    frame_dts = []
    measured_start = time.perf_counter()
    deadline = measured_start + float(a.duration)
    while time.perf_counter() < deadline:
        f0 = time.perf_counter()
        if not sim.done:
            sim.step(idle)
        else:
            # giữ vòng đo dù gather đã kết thúc
            pass
        frame_dts.append(time.perf_counter() - f0)
    measured_s = time.perf_counter() - measured_start
    frames = len(frame_dts)
    avg_fps = frames / measured_s if measured_s > 0 else 0.0
    n_low = max(1, int(__import__("math").ceil(0.01 * frames)))
    slow = sorted(frame_dts, reverse=True)[:n_low]
    mean_slow = sum(slow) / len(slow) if slow else 1.0
    p1_low_fps = (1.0 / mean_slow) if mean_slow > 0 else 0.0

    out = {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
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
