"""Soak headless: python3 -m chonoi.soak --seed 7 --days 10 --out soak.json"""

import argparse
import json
import sys
import time


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    from .contract import load_contract
    from .inputs import InputPlayer
    from .runner import Session

    tuning = load_contract()["tuning"]
    # Bot tất định: cập bến ngay, quán đứng yên, shop_done sớm mỗi Ngày
    # Dùng scenario rút ngắn để soak chạy nhanh trong lab
    scenario = {
        "day": {},
        "gather": {
            "hold": ["ca_loc", "bong_sung", "bong_sung"],
            "random_fish": False,
            "fish": [],
            "monsters": [],
            "nodes": [],
            "time_left_ticks": 30,
        },
        "quan": {"random_customers": False, "time_left_ticks": 30},
    }
    # Lặp frame: interact dock tick 0; shop_done sau quan
    frames = [
        {"tick": 0, "interact": True},
        {"tick": 40, "shop_done": True},
        {"tick": 80, "interact": True},
        {"tick": 120, "shop_done": True},
        {"tick": 160, "interact": True},
        {"tick": 200, "shop_done": True},
        {"tick": 240, "interact": True},
        {"tick": 280, "shop_done": True},
        {"tick": 320, "interact": True},
        {"tick": 360, "shop_done": True},
        {"tick": 400, "interact": True},
        {"tick": 440, "shop_done": True},
        {"tick": 480, "interact": True},
        {"tick": 520, "shop_done": True},
        {"tick": 560, "interact": True},
        {"tick": 600, "shop_done": True},
        {"tick": 640, "interact": True},
        {"tick": 680, "shop_done": True},
        {"tick": 720, "interact": True},
        {"tick": 760, "shop_done": True},
    ]

    t0 = time.perf_counter()
    crashes = 0
    results = []
    try:
        # chạy từng ngày riêng để ghi results[] ổn định
        days_completed = 0
        money = earned = 0
        reputation = tuning["quan"]["reputation_initial"]
        upgrades = {}
        for day_i in range(1, a.days + 1):
            sc = {
                "day": {"money": money, "earned": earned, "reputation": reputation, "upgrades": upgrades},
                "gather": dict(scenario["gather"]),
                "quan": dict(scenario["quan"]),
            }
            sess = Session("day", tuning, sc, a.seed + day_i, days=1)
            player = InputPlayer(frames)
            ticks_limit = 500
            while sess.tick < ticks_limit and not sess.done:
                inp = player.advance(sess.tick)
                sess.step(inp)
            if sess.done and sess.sim.reason == "days_complete":
                days_completed += 1
                money = sess.sim.money
                earned = sess.sim.earned
                reputation = sess.sim.reputation
                upgrades = dict(sess.sim.upgrades)
                results.append({
                    "day": day_i,
                    "earned": earned,
                    "reputation": reputation,
                    "score": earned + 100 * int(reputation),
                })
            else:
                crashes += 1
                break
    except Exception:
        crashes += 1

    duration_s = time.perf_counter() - t0
    out = {
        "days": a.days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
        f.write("\n")
    return 0 if crashes == 0 and days_completed == a.days else 1


if __name__ == "__main__":
    sys.exit(main())
