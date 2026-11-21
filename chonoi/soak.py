"""Soak headless (TICKET-04 mục 2): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Một tiến trình, MỘT DaySim chạy liền N Ngày (gather → quan → shop mỗi Ngày; kế hoạch D1–D5 lặp ở Ngày 6+).
Tiền, earned, uy tín, cấp nâng cấp, số Ngày và id cá thể đi xuyên suốt vì cùng một sim.
Bot tất định (không RNG riêng, không đồng hồ): cập bến ngay đầu buổi sáng, quán chạy hết ca, đóng Shop
ở bước đầu tiên. Không ghi bảng xếp hạng.

soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}
results lấy tại lúc Shop đóng (event shop_end). duration_s là số đo thời gian thực, bỏ qua khi so lặp.
"""

import argparse
import json
import math
import sys
import time


def bot_held(phase):
    """Giữ nút theo pha; thả ở pha khác nên mỗi lần vào pha có đúng một cạnh lên."""
    return {"interact": phase == "gather", "shop_done": phase == "shop"}


def run_soak(seed, days, tuning, max_ticks_per_day=22_200):
    from .inputs import InputState
    from .runner import Session

    sess = Session("day", tuning, {}, seed, days=days)
    mult = tuning["score"]["reputation_multiplier"]
    results, crashes = [], 0
    prev = bot_held(None)
    try:
        while not sess.done and sess.tick < days * max_ticks_per_day:
            held = bot_held(sess.sim.phase)
            edges = {b for b, v in held.items() if v and not prev[b]}
            prev = held
            for row in sess.step(InputState((0.0, 0.0), held, edges)):
                if row["name"] == "shop_end":
                    sim = sess.sim
                    results.append({"day": row["day"], "earned": sim.earned, "reputation": sim.reputation,
                                    "score": sim.earned + mult * math.floor(sim.reputation)})
    except Exception:  # noqa: BLE001 — soak đếm crash thay vì làm sập tiến trình
        crashes += 1
    return {"days": days, "days_completed": sess.sim.days_completed, "crashes": crashes, "results": results}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("--days phải >= 1\n")
        return 2

    from .contract import load_contract

    t0 = time.perf_counter()
    out = run_soak(a.seed, a.days, load_contract()["tuning"])
    out["duration_s"] = time.perf_counter() - t0
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
        f.write("\n")
    return 0 if out["crashes"] == 0 and out["days_completed"] == a.days else 1


if __name__ == "__main__":
    sys.exit(main())
