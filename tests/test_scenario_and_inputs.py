"""Kiểm định Contract C (inputs) và Contract D (scenario + mâu thuẫn -> mã 2)."""

import json
import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class InputsContract(unittest.TestCase):
    def test_missing_inputs_acts_as_standing_still(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [10, 5]}}})
            out = w.path("o.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            snaps = snapshots(read_jsonl(out))
            self.assertEqual(snaps[-1]["player"]["pos"], [10, 5])

    def test_invalid_inputs_rejected_with_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            bad_payloads = [
                {"frames": [], "extra": 1},
                {"frames": [{"tick": -1}]},
                {"frames": [{"tick": 2}, {"tick": 1}]},
                {"frames": [{"tick": 0, "move": [1.1, 0]}]},
                {"frames": [{"tick": 0, "move": [0, True]}]},
                {"frames": [{"tick": 0, "interact": "yes"}]},
                {"frames": [{"tick": 0, "catch": 1}]},
                {"frames": [{"tick": 0, "unknown_btn": True}]},
            ]
            for idx, payload in enumerate(bad_payloads):
                inp = write_json(w.path(f"bad_{idx}.json"), payload)
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--inputs", inp, "--out", out)
                self.assertEqual(code, 2, payload)
                self.assertFalse(os.path.exists(out))

    def test_wrong_phase_button_ignored_cleanly(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}, {"tick": 1, "catch": False}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--inputs", inp, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)


class ScenarioContract(unittest.TestCase):
    def test_empty_arrays_replace_defaults_not_merge(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"nodes": [], "fish": [], "random_fish": False}})
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            s = snapshots(read_jsonl(out))[0]
            self.assertEqual(s["nodes"], [])
            self.assertEqual(s["fish"], [])

    def test_natural_id_sorting_f2_before_f10(self):
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "random_fish": False,
                        "fish": [
                            {"id": "F10", "kind": "ca_loc", "pos": [20, 5]},
                            {"id": "F2", "kind": "ca_linh", "pos": [15, 5]},
                            {"id": "F1", "kind": "ca_loc", "pos": [10, 5]},
                        ],
                    }
                },
            )
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
            self.assertEqual(code, 0, err)
            ids = [f["id"] for f in snapshots(read_jsonl(out))[0]["fish"]]
            self.assertEqual(ids, ["F1", "F2", "F10"])

    def test_invalid_gather_scenarios_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            bad = [
                {"time_left_ticks": 0},
                {"time_left_ticks": 999999},
                {"random_fish": "no"},
                {"player": {"hp": 0}},
                {"player": {"hp": 99}},
                {"player": {"oxygen_ticks": -1}},
                {"player": {"oxygen_ticks": 99999}},
                {"player": {"pos": [10, 0], "oxygen_ticks": 0, "zero_oxy_ticks": 5}},
                {"player": {"pos": [10, 5], "oxygen_ticks": 100, "zero_oxy_ticks": 5}},
                {"player": {"pos": [10, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 60}},
                {"nodes": [{"id": "N1", "kind": "unknown_plant", "pos": [10, 0]}]},
                {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [10, 0], "extra": 1}]},
                {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 0.5]}]},
                {"fish": [{"id": "F1", "kind": "ca_linh", "pos": [10, 5], "speed": 2}]},
            ]
            for idx, blk in enumerate(bad):
                sc = write_json(w.path(f"g_{idx}.json"), {"gather": blk})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, blk)
                self.assertFalse(os.path.exists(out))

    def test_invalid_quan_scenarios_and_contradictions_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            bad = [
                {"random_customers": 1},
                {"reputation": 5.5},
                {"reputation": -0.1},
                {"stoves": [{"id": "B9"}]},
                {"stoves": [{"id": "B1", "extra": 1}]},
                {"tables": [{"id": "T9"}]},
                {"tables": [{"id": "T1", "extra": 1}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "extra": 1}]},
                {"hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60, "extra": 1},
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned"}]},
                {"stoves": [{"id": "B1", "state": "cooking", "cook_ticks_left": 0,
                             "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "mon_la"}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                                "order_status": "reserved", "eat_ticks_left": 10, "base_price": 60, "tip": 0}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating",
                                "order_status": "served", "eat_ticks_left": 10}]},
                {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned"}]},
                {"stock": {"ca_loc": 1},
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "reserved", "reserved": {"ca_linh": 1}}]},
                {"stock": {},
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "reserved"}]},
                {"hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                 "stoves": [{"id": "B1", "state": "ready",
                             "dish": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}],
                 "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                "order_status": "assigned"}]},
            ]
            for idx, blk in enumerate(bad):
                sc = write_json(w.path(f"q_{idx}.json"), {"quan": blk})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, blk)
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
