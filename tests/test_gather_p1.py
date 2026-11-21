"""Kiểm định cơ chế Gather Phase 1 (Lát 1: oxy/ngạt/ngất/dive/surface; Lát 2: hái/bắt cá/bến/kho)."""

import json
import os
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _tg():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


class GatherLat1OxygenChokeFaint(unittest.TestCase):
    def test_dive_and_surface_events_across_surface_depth(self):
        g = _tg()
        sd = g["surface_depth"]
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, sd]}, "fish": [], "random_fish": False}})
            inp = write_json(
                w.path("in.json"),
                frames({"tick": 0, "move": [0, 1]}, {"tick": 40, "move": [0, -1]}),
            )
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "90", "--scenario", sc,
                                     "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertGreaterEqual(len(events(rows, "dive")), 1)
            self.assertGreaterEqual(len(events(rows, "surface")), 1)

    def test_oxygen_drain_refill_and_empty_and_choke_at_t_plus_59(self):
        g = _tg()
        choke_iv = g["choke_interval_ticks"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 5], "oxygen_ticks": 2, "hp": 3, "zero_oxy_ticks": 0},
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            out = w.path("g.jsonl")
            # Tick 0->1: oxy 2->1; Tick 1->2: oxy 1->0 (oxygen_empty tại tick 2, zero_oxy_ticks=1)
            # Đủ 60 tick ở oxy=0 -> choke lần đầu ở tick 2 + 59 = 61
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(2 + choke_iv),
                                     "--scenario", sc, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            empty_evs = events(rows, "oxygen_empty")
            self.assertEqual([e["tick"] for e in empty_evs], [2])
            choke_evs = events(rows, "choke")
            self.assertEqual(len(choke_evs), 1)
            self.assertEqual(choke_evs[0]["tick"], 1 + choke_iv)
            self.assertEqual(choke_evs[0]["data"]["hp"], 2)

    def test_surface_on_exact_choke_tick_prevents_choke_and_refills(self):
        g = _tg()
        with Workdir() as w:
            # Đứng ngay sát mặt nước (d=0.6), zero_oxy_ticks=59, oxy=0: nếu ở dưới nước thêm 1 tick sẽ ngạt
            # Bơi lên trên ở tick 0 -> cuối tick 0 ở d <= 0.5 -> hồi oxy, reset zero_oxy_ticks, không choke
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, g["surface_depth"] + 0.05], "vel": [0, -g["swim_speed"]],
                                   "oxygen_ticks": 0, "hp": 3, "zero_oxy_ticks": g["choke_interval_ticks"] - 1},
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [0, -1]}))
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "choke"), [])
            s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]["player"]
            self.assertTrue(s1["at_surface"])
            self.assertEqual(s1["hp"], 3)
            self.assertEqual(s1["zero_oxy_ticks"], 0)
            self.assertEqual(s1["oxygen_ticks"], g["oxygen_refill_per_tick"])

    def test_faint_drops_hold_lifo_and_writes_empty_inventory(self):
        g = _tg()
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 5], "oxygen_ticks": 0, "hp": 1,
                                   "zero_oxy_ticks": g["choke_interval_ticks"] - 1},
                        "hold": ["ca_loc", "bong_sung", "ca_linh"],
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            out = w.path("g.jsonl")
            inv = w.path("catch.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inventory-out", inv, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            faint_evs = events(rows, "faint")
            self.assertEqual(len(faint_evs), 1)
            self.assertEqual(faint_evs[0]["data"]["cause"], "choke")
            self.assertEqual(faint_evs[0]["data"]["hp"], 0)
            self.assertEqual(faint_evs[0]["data"]["lost"], ["ca_linh", "bong_sung", "ca_loc"])
            g_end = events(rows, "gather_end")
            self.assertEqual(len(g_end), 1)
            self.assertEqual(g_end[0]["data"]["reason"], "fainted")
            self.assertEqual(g_end[0]["data"]["inventory"], {"items": {}})
            self.assertEqual(rows[-1]["reason"], "fainted")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class GatherLat2NodesCatchDock(unittest.TestCase):
    def test_dock_has_priority_over_node_even_at_exact_boundary(self):
        g = _tg()
        dx, dd = g["dock_pos"]
        r = g["dock_radius"]
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [dx + r, dd]},
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [dx + r, 0]}],
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(events(rows, "gather"), [])
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")

    def test_gather_surface_only_nearest_tiebreak_id_and_regrow(self):
        g = _tg()
        regrow_ticks = int(round(g["regrow_s"] * 60))
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 0]},
                        "nodes": [
                            {"id": "N2", "kind": "bong_sung", "pos": [20 + g["interact_radius"], 0]},
                            {"id": "N1", "kind": "bong_dien_dien", "pos": [20 - g["interact_radius"], 0]},
                        ],
                        "fish": [],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": True},  # giữ nút không được lặp
                    {"tick": 2, "interact": False},
                    {"tick": regrow_ticks + 1, "interact": True},  # ngay khi regrow xong phải hái lại được
                ),
            )
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(regrow_ticks + 3),
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            g_evs = events(rows, "gather")
            self.assertEqual(len(g_evs), 2)
            self.assertEqual(g_evs[0]["data"]["node_id"], "N1")
            self.assertEqual(g_evs[0]["data"]["kind"], "bong_dien_dien")
            self.assertEqual(g_evs[1]["data"]["node_id"], "N2")  # hoặc N1 nếu đã mọc lại và hòa id
            regrown = events(rows, "node_regrown")
            self.assertEqual([e["data"]["node_id"] for e in regrown], ["N1"])
            self.assertEqual(regrown[0]["tick"], 1 + regrow_ticks)

    def test_catch_underwater_yield_cooldown_and_hold_full(self):
        g = _tg()
        cd_ticks = int(round(g["catch_cooldown_s"] * 60))
        cap = g["hold_capacity"]
        with Workdir() as w:
            # Giỏ còn trống 2 chỗ: cá linh yield=3 -> hold_full, không thử cá lóc bên cạnh, không tiêu cooldown
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 5]},
                        "hold": ["bong_sung"] * (cap - 2),
                        "nodes": [],
                        "fish": [
                            {"id": "F1", "kind": "ca_linh", "pos": [20.5, 5]},
                            {"id": "F2", "kind": "ca_loc", "pos": [21.0, 5]},
                        ],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(
                w.path("in.json"),
                frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False}),
            )
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            hf = events(rows, "hold_full")
            self.assertEqual(len(hf), 1)
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
            self.assertEqual(events(rows, "fish_caught"), [])
            s1 = [s for s in snapshots(rows) if s["tick"] == 1][0]
            self.assertEqual(len(s1["fish"]), 2)
            self.assertEqual(s1["player"]["catch_cd_ticks"], 0)

        # Kiểm tra bắt thành công + cooldown L dùng lại đúng tại t+L
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [20, 5]},
                        "nodes": [],
                        "fish": [
                            {"id": "F1", "kind": "ca_loc", "pos": [20.5, 5]},
                            {"id": "F2", "kind": "ca_linh", "pos": [20 + g["catch_radius"], 5]},
                        ],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "catch": True},
                    {"tick": 1, "catch": False},
                    {"tick": max(2, cd_ticks - 1), "catch": True},  # chưa hết cooldown -> bỏ qua
                    {"tick": max(3, cd_ticks), "catch": False},
                    {"tick": cd_ticks + 1, "catch": True},  # đủ cooldown -> bắt F2
                ),
            )
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", str(cd_ticks + 3),
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            fc = events(rows, "fish_caught")
            self.assertEqual(len(fc), 2)
            self.assertEqual(fc[0]["data"], {"fish_id": "F1", "kind": "ca_loc", "yield": 1})
            self.assertEqual(fc[1]["data"], {"fish_id": "F2", "kind": "ca_linh", "yield": 3})


if __name__ == "__main__":
    unittest.main()
