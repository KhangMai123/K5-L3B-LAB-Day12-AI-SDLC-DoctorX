"""Phase 3: độ tươi / spoiled / kho cá thể."""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, write_json


class FreshnessP3(unittest.TestCase):
    def test_spoiled_at_threshold_on_first_gather_step(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                    "random_fish": False,
                    "monsters": [],
                    "fish": [],
                    "nodes": [],
                }
            })
            out = w.path("g.jsonl")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--scenario", sc, "--ticks", "1", "--out", out,
            )
            self.assertEqual(code, 0, err)
            sp = events(read_jsonl(out), "spoiled")
            self.assertEqual(len(sp), 1)
            self.assertEqual(sp[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})

    def test_count_inventory_rejected(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 1}})
            code, _ = run_headless(
                "--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "0",
                "--out", w.path("q.jsonl"),
            )
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
