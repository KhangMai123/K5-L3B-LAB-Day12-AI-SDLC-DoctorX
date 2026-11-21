"""Smoke Phase 2: --mode day, cá bơi/sinh, Cá Sấu tối thiểu."""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class DayModeP2(unittest.TestCase):
    def test_day_ticks_zero_emits_end_with_days_completed(self):
        with Workdir() as w:
            out = w.path("d.jsonl")
            code, err = run_headless(
                "--mode", "day", "--seed", "1", "--days", "1", "--ticks", "0", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(rows[0]["type"], "snapshot")
            self.assertEqual(rows[0]["mode"], "day")
            self.assertEqual(rows[0]["phase"], "gather")
            self.assertEqual(rows[0]["day"], 1)
            self.assertIn("day_plan", rows[0])
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["days_completed"], 0)

    def test_day_dock_then_shop_done_completes_one_day(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "day": {},
                "gather": {
                    "hold": ["ca_loc", "bong_sung", "bong_sung"],
                    "random_fish": False,
                    "fish": [],
                    "monsters": [],
                    "nodes": [],
                },
                "quan": {"random_customers": False, "time_left_ticks": 2},
            })
            # tick0 interact dock → gather_end; quan chạy 2 tick rồi shop; shop_done
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 5, "shop_done": True},
            ))
            out = w.path("d.jsonl")
            code, err = run_headless(
                "--mode", "day", "--seed", "42", "--days", "1", "--scenario", sc,
                "--inputs", inp, "--ticks", "30", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertTrue(events(rows, "day_start"))
            self.assertTrue(events(rows, "day_plan"))
            self.assertTrue(events(rows, "gather_end"))
            self.assertTrue(events(rows, "quan_end"))
            self.assertTrue(events(rows, "shop_end"))
            end = rows[-1]
            self.assertEqual(end["reason"], "days_complete")
            self.assertEqual(end["days_completed"], 1)

    def test_monster_present_on_day1_gather(self):
        with Workdir() as w:
            out = w.path("g.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--out", out)
            self.assertEqual(code, 0, err)
            s = snapshots(read_jsonl(out))[0]
            ids = [m["id"] for m in s["monsters"]]
            self.assertIn("M1", ids)
            self.assertNotIn("M2", ids)


if __name__ == "__main__":
    unittest.main()
