"""Kiểm định cơ chế Quán Phase 1 theo PRD-0 Test Contract v1.0 (Lát 3 & Lát 4)."""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tq():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]


class QuanLat3CustomersAndReservation(unittest.TestCase):
    def test_customer_spawns_on_first_tick_even_with_short_shift_and_reserves_stock(self):
        t = _tq()
        q = t["quan"]
        first = q["first_customer_tick"]
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            sc = write_json(w.path("sc.json"), {"quan": {"time_left_ticks": first + 5}})
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--inventory", inv, "--scenario", sc,
                                     "--ticks", str(first + 1), "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            arr = events(rows, "customer_arrived")
            self.assertEqual(len(arr), 1)
            self.assertEqual(arr[0]["tick"], first)
            self.assertEqual(arr[0]["data"].get("table_id"), "T1")
            self.assertEqual(arr[0]["data"].get("dish_id"), "ca_loc_nuong_trui")
            self.assertIn("order_id", arr[0]["data"])
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
            self.assertEqual(nd[0]["data"], {})
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
            self.assertEqual(left[0]["data"].get("order_id"), "C1")
            self.assertEqual(left[0]["data"]["reason"], "patience")
            expected_rep = max(q["reputation_min"], q["reputation_initial"] + q["left_reputation_delta"])
            self.assertAlmostEqual(left[0]["data"]["reputation"], expected_rep, places=2)

    def test_inventory_exceeded_by_scenario_reserved_exits_2(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 0}})
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "customers": [
                            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"}
                        ],
                    }
                },
            )
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--inventory", inv, "--scenario", sc,
                                   "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 2)


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

            cs = events(rows, "cook_started")
            self.assertEqual(len(cs), 1)
            self.assertEqual(cs[0]["data"], {
                "stove_id": "B1",
                "order_id": "C1",
                "dish_id": "ca_loc_nuong_trui",
                "items": ["ca_loc"],
                "base_price": dish["price"],
            })
            dr = events(rows, "dish_ready")
            self.assertEqual(dr[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})
            dp = events(rows, "dish_picked")
            self.assertEqual(dp[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})

            srv = events(rows, "served")
            self.assertEqual(len(srv), 1)
            expected_tip = math.floor(dish["price"] * q["tip_rate"])
            self.assertEqual(srv[0]["data"].get("order_id"), "C1")
            self.assertEqual(srv[0]["data"].get("base_price"), dish["price"])
            self.assertIn("patience_ticks_left", srv[0]["data"])
            self.assertEqual(srv[0]["data"]["tip"], expected_tip)

            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"], {
                "order_id": "C1",
                "table_id": "T1",
                "base_price": dish["price"],
                "tip": expected_tip,
                "amount": dish["price"] + expected_tip,
                "reason": "finished_eating",
            })
            end = rows[-1]
            self.assertEqual(end["money"], dish["price"] + expected_tip)
            self.assertEqual(end["earned"], dish["price"] + expected_tip)

    def test_serve_on_exact_zero_patience_tick_still_valid(self):
        t = _tq()
        q = t["quan"]
        dish = t["menu"]["ca_loc_nuong_trui"]
        t1_pos = q["tables"][0]["pos"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "player": {"pos": t1_pos},
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]},
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "patience_ticks_left": 1,
                                "order_status": "assigned",
                            }
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", "2", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "served")), 1)
            self.assertEqual(events(rows, "customer_left"), [])

    def test_interact_prefers_stove_on_tie_and_does_not_fallback_to_table(self):
        t = _tq()
        q = t["quan"]
        dish = t["menu"]["ca_loc_nuong_trui"]
        b1_pos = q["stoves"][0]["pos"]
        t1_pos = q["tables"][0]["pos"]
        mid = [(b1_pos[0] + t1_pos[0]) / 2, (b1_pos[1] + t1_pos[1]) / 2]
        # Đặt bếp B1 ở [6, 5] và bàn T1 ở [10, 5] nếu trong interact_radius? Ở đây đặt player ở giữa không quá interact_radius,
        # dùng stove pos cập nhật trong scenario để hai đối tượng đúng bằng nhau trong bán kính.
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "player": {"pos": [8, 5]},
                        "stoves": [{"id": "B1", "pos": [7, 5], "state": "cooking", "cook_ticks_left": 50,
                                    "dish": {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]}}],
                        "tables": [{"id": "T1", "pos": [9, 5]}],
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]},
                        "customers": [
                            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}
                        ],
                    }
                },
            )
            # Ở đây C2 không nằm trong customers nên scenario hợp lệ sẽ báo mã 2; dùng 1 khách với B1 idle và stock rỗng?
            # Nếu B1 cooking của C1 và hand trống? Không, muốn B1 không tương tác được thì B1 cooking của C1 và player đứng gần B1 hơn T1,
            # hoặc dùng B1 ready + hand đã cầm món khác? Khi chỉ có 1 khách thì chỉ 1 món assigned.
            # Thay vào đó: B1 idle (không có đơn reserved nào) + hand cầm món cho C1 tại T1 -> B1 idle + hand != None vẫn là interact không hợp lệ tại B1!
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "player": {"pos": [8, 5]},
                        "stoves": [{"id": "B1", "pos": [7, 5]}],
                        "tables": [{"id": "T1", "pos": [9, 5]}],
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]},
                        "customers": [
                            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "served"), [])
            self.assertEqual(events(rows, "cook_started"), [])

    def test_closing_pays_eating_just_served_clears_stoves_and_no_spawn(self):
        t = _tq()
        q = t["quan"]
        dish = t["menu"]["ca_loc_nuong_trui"]
        t1_pos = q["tables"][0]["pos"]
        with Workdir() as w:
            # 1) Đúng tick closing: khách C1 vừa được served ở tick cuối phải được paid(reason="closing")
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": True,
                        "time_left_ticks": 1,
                        "player": {"pos": t1_pos},
                        "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]},
                        "customers": [
                            {
                                "id": "C1",
                                "table_id": "T1",
                                "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned",
                            }
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out = w.path("q1.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", "5", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "served")), 1)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"]["reason"], "closing")
            self.assertEqual(events(rows, "customer_left"), [])

        with Workdir() as w:
            # 2) Closing khi còn khách waiting có món đang nấu trên bếp:
            #    - khách waiting rời với closing không trừ rep
            #    - món trên bếp bị hủy (bếp về idle trong snapshot cuối)
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "time_left_ticks": 2,
                        "stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 50,
                                    "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": dish["price"]}}],
                        "customers": [
                            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}
                        ],
                    }
                },
            )
            out = w.path("q2.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--ticks", "5", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["data"]["reason"], "closing")
            self.assertAlmostEqual(left[0]["data"]["reputation"], q["reputation_initial"], places=2)
            last_snap = snapshots(rows)[-1]
            self.assertEqual(last_snap["stoves"][0]["state"], "idle")
            self.assertIsNone(last_snap["stoves"][0]["dish"])
            self.assertEqual(events(rows, "quan_end")[0]["data"]["reason"], "time")

        with Workdir() as w:
            # 3) Đúng tick closing trùng first_customer_tick dù còn bàn trống và đủ kho: không sinh khách mới
            first = q["first_customer_tick"]
            sc = write_json(
                w.path("sc.json"),
                {"quan": {"random_customers": True, "time_left_ticks": first, "stock": {"ca_loc": 5}}},
            )
            out = w.path("q3.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--ticks", str(first + 5), "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])
            self.assertEqual(events(rows, "customer_left"), [])

    def test_ready_ticks_starts_at_zero_and_never_burns(self):
        t = _tq()
        dish = t["menu"]["ca_loc_nuong_trui"]
        cook_ticks = int(round(dish["cook_s"] * 60))
        b1_pos = t["quan"]["stoves"][0]["pos"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "quan": {
                        "random_customers": False,
                        "player": {"pos": b1_pos},
                        "stock": {"ca_loc": 1},
                        "customers": [
                            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"}
                        ],
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc,
                                     "--inputs", inp, "--ticks", str(cook_ticks + 5),
                                     "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1 + cook_ticks]["stoves"][0]["state"], "ready")
            self.assertEqual(snaps[1 + cook_ticks]["stoves"][0]["ready_ticks"], 0)
            self.assertEqual(snaps[2 + cook_ticks]["stoves"][0]["ready_ticks"], 1)


if __name__ == "__main__":
    unittest.main()
