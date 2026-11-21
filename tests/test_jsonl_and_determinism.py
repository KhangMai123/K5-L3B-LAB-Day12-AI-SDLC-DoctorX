"""Kiểm định schema JSONL, thứ tự snapshot/event/end, tính tất định từng byte và làm tròn tọa độ."""

import json
import math
import os
import unittest

from helpers import ROOT, Workdir, frames, read_jsonl, run_headless, snapshots, write_json


def _contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


class JsonlAndDeterminism(unittest.TestCase):
    def test_snapshot_cadence_and_event_ordering(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"time_left_ticks": 5}})
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--snapshot-every", "2", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snaps = snapshots(rows)
            self.assertEqual([s["tick"] for s in snaps], [0, 2, 4, 5])
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "time")
            self.assertEqual(rows[-1]["state"], "finished")
            # event ở tick 5 phải nằm TRƯỚC snapshot tick 5
            idx_ev = next(i for i, r in enumerate(rows) if r["type"] == "event" and r["name"] == "gather_end")
            idx_sn = next(i for i, r in enumerate(rows) if r["type"] == "snapshot" and r["tick"] == 5)
            self.assertLess(idx_ev, idx_sn)

    def test_common_snapshot_and_score_formula(self):
        c = _contract()
        mult = c["tuning"]["score"]["reputation_multiplier"]
        with Workdir() as w:
            for mode in ("gather", "quan"):
                out = w.path(f"{mode}.jsonl")
                code, err = run_headless("--mode", mode, "--seed", "7", "--ticks", "0", "--out", out)
                self.assertEqual(code, 0, err)
                rows = read_jsonl(out)
                s = rows[0]
                for k in ("type", "tick", "sim_tick", "mode", "phase", "phase_tick", "state",
                          "time_left_ticks", "money", "earned", "reputation", "score"):
                    self.assertIn(k, s, (mode, k))
                self.assertEqual(s["score"], s["earned"] + mult * math.floor(s["reputation"]))
                end = rows[-1]
                for k in ("type", "ticks", "sim_tick", "mode", "state", "reason", "money", "earned", "reputation", "score"):
                    self.assertIn(k, end, (mode, k))
                self.assertEqual(end["reason"], "tick_limit")

    def test_quan_determinism_byte_for_byte(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 5, "bong_sung": 4, "ca_linh": 6, "bong_dien_dien": 2}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [-1, 1]}, {"tick": 100, "move": [0, 0]}))
            for i in (1, 2):
                code, err = run_headless("--mode", "quan", "--seed", "123", "--ticks", "300",
                                         "--inventory", inv, "--inputs", inp, "--out", w.path(f"q{i}.jsonl"))
                self.assertEqual(code, 0, err)
            with open(w.path("q1.jsonl"), "rb") as a, open(w.path("q2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())

    def test_coordinates_rounded_to_at_most_3_decimals(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [1, 1]}))
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "15",
                                     "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            with open(out, encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)
                    if row["type"] == "snapshot":
                        for val in row["player"]["pos"] + row["player"]["vel"]:
                            self.assertEqual(round(val, 3), val)


if __name__ == "__main__":
    unittest.main()
