"""Kiểm định cơ chế Quán Phase 1 (Lát 3: khách/giữ chỗ/kiên nhẫn; Lát 4: bếp/bưng/phục vụ/tiền/uy tín)."""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tq():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]


class QuanLat3CustomersAndReservation(unittest.TestCase):
    def test_customer_spawns_on_first_tick_and_reserves_stock(self):
        t = _tq()
        q = t["quan"]
        first = q["first_customer_tick"]
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", inv,
                                     "--ticks", str(first + 1), "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], first)
            self.assertEqual(arr[0]["data"]["table_id"], "T1")
            self.assertEqual(arr[0]["data"]["dish_id"], "ca_loc_nuong_trui")
            # Khách mới không giảm kiên nhẫn ở tick vừa sinh
            snap = [s for s in snapshots(rows) if s["tick"] == first][0]
            self.assertEqual(len(snap["customers"]), 1)
            self.assertEqual(snap["customers"][0]["patience_ticks_left"], int(round(q["patience_s"] * 60)))

    def test_no_dish_when_available_stock_insufficient(self):
        t = _tq()
        first = t["quan"]["first_customer_tick"]
        with Workdir() as w:
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(first + 1), "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            nd = events(rows, "no_dish")
            self.assertEqual(len(nd), 1)
            self.assertEqual(nd[0]["tick"], first)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_waiting_customer_leaves_on_zero_patience_and_drops_reputation(self):
        t = _tq()
        q = t["quan"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "stock": {"ca_loc": 1},
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "patience_ticks_left": 2,
                                "order_status": "reserved",
                            }
                        ],
                    }
                },
            )
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--ticks", "3", "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 2)
            self.assertEqual(left[0]["data"]["reason"], "patience")
            expected_rep = max(q["reputation_min"], q["reputation_initial"] + q["left_reputation_delta"])
            self.assertAlmostEqual(left[0]["data"]["reputation"], expected_rep, places=2)


class QuanLat4CookServePayClose(unittest.TestCase):
    def test_full_cook_pick_serve_pay_with_tip_and_reputation(self):
        t = _tq()
        q = t["quan"]
        dish = t["menu"]["ca_loc_nuong_trui"]
        cook_ticks = int(round(dish["cook_s"] * 60))
        eat_ticks = int(round(q["eat_s"] * 60))
        b1_pos = q["stoves"][0]["pos"]
        t1_pos = q["tables"][0]["pos"]
        with Workdir() as w:
            # Đặt sẵn khách C1 đang chờ, chạy đủ bước ở bếp B1 rồi chuyển sang bàn T1
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "player": {"pos": b1_pos},
                        "stock": {"ca_loc": 1},
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "order_status": "reserved",
                            }
                        ],
                    }
                },
            )
            # Đứng ở bếp B1 tại tick 0 -> cook_started; sau cook_ticks -> dish_ready;
            # nhấc món tại tick cook_ticks + 1 -> dish_picked;
            # đi bộ sang bàn T1 (khoảng cách ~9.2m, tốc độ 4m/s -> ~150 ticks) rồi interact
            pick_tick = cook_ticks + 2
            dx = t1_pos[0] - b1_pos[0]
            dz = t1_pos[1] - b1_pos[1]
            dist = math.hypot(dx, dz)
            walk_ticks = math.ceil((dist / q["walk_speed"]) * 60) + q["ramp_max_ticks"] + 5
            serve_tick = pick_tick + 2 + walk_ticks
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": pick_tick, "interact": True},
                    {"tick": pick_tick + 1, "interact": False, "move": [dx / dist, dz / dist]},
                    {"tick": serve_tick - 1, "move": [0, 0]},
                    {"tick": serve_tick, "interact": True},
                    {"tick": serve_tick + 1, "interact": False},
                ),
            )
            total_ticks = serve_tick + eat_ticks + 10
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", str(total_ticks), "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "cook_started")), 1)
            self.assertEqual(len(events(rows, "dish_ready")), 1)
            self.assertEqual(len(events(rows, "dish_picked")), 1)
            srv = events(rows, "served")
            self.assertEqual(len(srv), 1)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"]["reason"], "finished_eating")
            expected_tip = math.floor(dish["price"] * q["tip_rate"])
            self.assertEqual(paid[0]["data"]["tip"], expected_tip)
            self.assertEqual(paid[0]["data"]["amount"], dish["price"] + expected_tip)
            end = rows[-1]
            self.assertEqual(end["money"], dish["price"] + expected_tip)
            self.assertEqual(end["earned"], dish["price"] + expected_tip)

    def test_closing_pays_eating_and_dismisses_waiting_without_rep_penalty(self):
        t = _tq()
        q = t["quan"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "time_left_ticks": 2,
                        "stock": {"ca_loc": 1},
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "order_status": "reserved",
                            }
                        ],
                    }
                },
            )
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc, "--ticks", "5", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["data"]["reason"], "closing")
            self.assertAlmostEqual(left[0]["data"]["reputation"], q["reputation_initial"], places=2)
            q_end = events(rows, "quan_end")
            self.assertEqual(len(q_end), 1)
            self.assertEqual(q_end[0]["data"]["reason"], "time")


if __name__ == "__main__":
    unittest.main()
