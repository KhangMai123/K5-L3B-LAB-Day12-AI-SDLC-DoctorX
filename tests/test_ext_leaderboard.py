"""Mở rộng `leaderboard` (TICKET-04 mục 3). Mỗi test dùng store riêng trong thư mục tạm."""

import json
import os
import subprocess
import sys
import unittest

from chonoi import leaderboard
from chonoi.contract import load_contract
from chonoi.errors import BadInput

from helpers import ROOT, Workdir, read_jsonl, run_headless, write_json

TICKS_5_DAYS = "120000"


def day5(w, store, name="Út Sen", seed="42", extra=()):
    return run_headless("--mode", "day", "--seed", seed, "--days", "5", "--ticks", TICKS_5_DAYS,
                        "--snapshot-every", "5000", "--out", w.path(f"d{seed}.jsonl"),
                        "--leaderboard", store, "--player-name", name, *extra)


def entries(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["entries"]


class LeaderboardExt(unittest.TestCase):
    def test_manifest_declares_leaderboard(self):
        self.assertIn("leaderboard", load_contract()["extensions"])

    def test_five_standard_days_record_exactly_one_entry(self):
        with Workdir() as w:
            store = w.path("store.json")
            code, err = day5(w, store)
            self.assertEqual(code, 0, err)
            end = read_jsonl(w.path("d42.jsonl"))[-1]
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(entries(store), [{"name": "Út Sen", "score": end["score"],
                                               "days_completed": 5, "seed": 42}])

    def test_jsonl_identical_with_and_without_leaderboard(self):
        with Workdir() as w:
            day5(w, w.path("s.json"))
            code, _ = run_headless("--mode", "day", "--seed", "42", "--days", "5", "--ticks", TICKS_5_DAYS,
                                   "--snapshot-every", "5000", "--out", w.path("plain.jsonl"))
            self.assertEqual(code, 0)
            with open(w.path("d42.jsonl"), "rb") as a, open(w.path("plain.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())

    def test_no_entry_when_not_five_days_or_with_scenario_or_cut_short(self):
        with Workdir() as w:
            store = w.path("store.json")
            run_headless("--mode", "day", "--seed", "1", "--days", "1", "--ticks", "30000", "--out", w.path("a.jsonl"),
                         "--leaderboard", store, "--player-name", "A")
            run_headless("--mode", "day", "--seed", "1", "--days", "5", "--ticks", "100", "--out", w.path("b.jsonl"),
                         "--leaderboard", store, "--player-name", "A")
            write_json(w.path("sc.json"), {"day": {}})
            day5(w, store, extra=("--scenario", w.path("sc.json")))
            self.assertFalse(os.path.exists(store))

    def test_bad_flag_pairs_exit_2(self):
        with Workdir() as w:
            store = w.path("store.json")
            out = w.path("x.jsonl")
            for args in (("--mode", "day", "--leaderboard", store),
                         ("--mode", "day", "--player-name", "A"),
                         ("--mode", "gather", "--leaderboard", store, "--player-name", "A"),
                         ("--mode", "day", "--leaderboard", store, "--player-name", "  ")):
                code, _ = run_headless(*args, "--seed", "1", "--ticks", "1", "--out", out)
                self.assertEqual(code, 2, args)

    def test_sort_desc_ties_keep_record_order_and_top10(self):
        with Workdir() as w:
            store = w.path("store.json")
            for name, score in [("a", 100), ("b", 300), ("c", 100), ("d", 300)]:
                leaderboard.record(store, name, score, 5, 1)
            self.assertEqual([e["name"] for e in leaderboard.load(store)], ["b", "d", "a", "c"])
            for i in range(10):
                leaderboard.record(store, f"x{i}", 200, 5, 1)
            got = leaderboard.load(store)
            self.assertEqual(len(got), 10)
            self.assertEqual([e["name"] for e in got[:3]], ["b", "d", "x0"])

    def test_corrupt_store_rejected(self):
        with Workdir() as w:
            store = w.path("store.json")
            write_json(store, {"entries": [{"name": "", "score": 1, "days_completed": 5, "seed": 1}]})
            with self.assertRaises(BadInput):
                leaderboard.load(store)

    def test_export_via_run_cmd(self):
        with Workdir() as w:
            store, out = w.path("store.json"), w.path("out.json")
            leaderboard.record(store, "Má Tư", 500, 5, 7)
            leaderboard.record(store, "Út Sen", 900, 5, 42)
            env = dict(os.environ, PYTHONPATH=ROOT)
            p = subprocess.run([sys.executable, "-m", "chonoi.live", "--mode", "gather",
                                "--export-leaderboard", out, "--leaderboard", store],
                               cwd=ROOT, capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual([e["name"] for e in entries(out)], ["Út Sen", "Má Tư"])


if __name__ == "__main__":
    unittest.main()
