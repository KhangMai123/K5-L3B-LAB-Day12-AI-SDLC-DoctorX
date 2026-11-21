"""TICKET-04 mục 2: soak nhiều Ngày trong một tiến trình, một DaySim."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.runner import Session
from chonoi.soak import run_soak

from helpers import ROOT, Workdir

T = load_contract()["tuning"]


class SoakP4(unittest.TestCase):
    def test_six_days_complete_no_crash_results_per_shop_close(self):
        out = run_soak(7, 6, T)
        self.assertEqual((out["days"], out["days_completed"], out["crashes"]), (6, 6, 0))
        self.assertEqual([r["day"] for r in out["results"]], [1, 2, 3, 4, 5, 6])
        for r in out["results"]:
            self.assertEqual(set(r), {"day", "earned", "reputation", "score"})

    def test_repeatable_without_wall_clock(self):
        self.assertEqual(run_soak(7, 3, T), run_soak(7, 3, T))

    def test_plan_cycles_d1_d5_from_day_6(self):
        sim = Session("day", T, {}, 1, days=6).sim
        self.assertEqual(sim._plan_for(6)["dishes"], T["day_plan"][0]["dishes"])
        self.assertEqual(sim._plan_for(10)["dishes"], T["day_plan"][4]["dishes"])

    def test_cli_writes_all_fields(self):
        import subprocess
        import sys
        with Workdir() as w:
            p = subprocess.run([sys.executable, "-m", "chonoi.soak", "--seed", "7", "--days", "2",
                                "--out", w.path("s.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(w.path("s.json"), encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data), {"days", "days_completed", "crashes", "results", "duration_s"})


if __name__ == "__main__":
    unittest.main()
