"""Kiểm định Contract G (file kho) và smoke test hai tiến trình độc lập theo PRD-0."""

import json
import os
import unittest

from helpers import inv_items_from_counts, stock_counts,  Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class InventoryContractAndSmoke(unittest.TestCase):
    def test_prd0_two_process_smoke_in_temp_dir(self):
        with Workdir() as w:
            dock = write_json(w.path("dock.json"), {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
            inp = write_json(w.path("dock-inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
            g_out = w.path("gather.jsonl")
            catch_inv = w.path("catch.json")
            q_out = w.path("quan.jsonl")

            code, err = run_headless(
                "--mode", "gather", "--seed", "42", "--scenario", dock,
                "--inputs", inp, "--ticks", "1", "--out", g_out, "--inventory-out", catch_inv,
            )
            self.assertEqual(code, 0, err)
            g_rows = read_jsonl(g_out)
            g_end = events(g_rows, "gather_end")
            self.assertEqual(len(g_end), 1)
            self.assertEqual(g_end[0]["data"]["reason"], "docked")

            with open(catch_inv, encoding="utf-8") as f:
                inv_data = json.load(f)
            self.assertEqual(stock_counts(inv_data["items"]), {"bong_sung": 2, "ca_loc": 1})

            code, err = run_headless(
                "--mode", "quan", "--seed", "42", "--inventory", catch_inv,
                "--ticks", "0", "--out", q_out,
            )
            self.assertEqual(code, 0, err)
            q_snap = snapshots(read_jsonl(q_out))[0]
            self.assertEqual(stock_counts(q_snap["stock"]), {"bong_sung": 2, "ca_loc": 1})
            self.assertEqual(q_snap["money"], 0)
            self.assertEqual(q_snap["earned"], 0)

    def test_inventory_sentinel_not_overwritten_when_tick_limit(self):
        with Workdir() as w:
            inv_out = w.path("catch.json")
            sentinel = '{"items":{"ca_loc":99}}'
            with open(inv_out, "w", encoding="utf-8") as f:
                f.write(sentinel)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--inventory-out", inv_out, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv_out, encoding="utf-8") as f:
                self.assertEqual(f.read(), sentinel)

    def test_inventory_large_qty_beyond_hold_capacity_allowed_in_quan(self):
        with Workdir() as w:
            inv = write_json(w.path("big.json"), inv_items_from_counts({"ca_linh": 50, "bong_sung": 40}))
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", out)
            self.assertEqual(code, 0, err)
            self.assertEqual(stock_counts(snapshots(read_jsonl(out))[0]["stock"]), {"bong_sung": 40, "ca_linh": 50})

    def test_inventory_rejects_bad_schemas_with_exit_2(self):
        with Workdir() as w:
            out = w.path("q.jsonl")
            bad_invs = [
                {},
                
                {"items": {"ca_loc": True}},
                {"items": {"ca_loc": -2}},
                {"items": {"ca_loc": 1.5}},
                {"items": {"mon_la": 1}},
                {"items": {}, "extra": 1},
            ]
            for idx, payload in enumerate(bad_invs):
                p = write_json(w.path(f"bad_{idx}.json"), payload)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p, "--out", out)
                self.assertEqual(code, 2, payload)
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
