"""Test Contract v1.1 mục 4.4–4.5 (vỏ event của --mode day) + v1.2 id cá thể xuyên Ngày."""

import unittest

from helpers import Workdir, read_jsonl, run_headless, write_json

HOLD = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100}]


def run_two_days(w):
    write_json(w.path("sc.json"), {"day": {"money": 200, "earned": 200},
                                   "gather": {"hold": HOLD, "random_fish": False}})
    write_json(w.path("in.json"), {"frames": [{"tick": 0, "interact": True}]})
    code, err = run_headless("--mode", "day", "--seed", "1", "--days", "2", "--ticks", "11500",
                             "--scenario", w.path("sc.json"), "--inputs", w.path("in.json"),
                             "--out", w.path("d.jsonl"))
    assert code == 0, err
    return read_jsonl(w.path("d.jsonl"))


def ev(rows, name):
    return [(r["tick"], r["phase"], r["day"]) for r in rows if r["type"] == "event" and r["name"] == name]


class DayEnvelope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with Workdir() as w:
            cls.rows = run_two_days(w)

    def test_first_row_is_tick0_snapshot_then_day_opening_events_at_tick0(self):
        self.assertEqual((self.rows[0]["type"], self.rows[0]["tick"]), ("snapshot", 0))
        opening = [(r["name"], r["tick"], r["phase"], r["day"]) for r in self.rows[1:4]]
        self.assertEqual(opening, [("day_start", 0, "gather", 1), ("day_plan", 0, "gather", 1),
                                   ("phase_start", 0, "gather", 1)])

    def test_end_events_carry_old_phase_and_phase_start_new_phase_same_tick(self):
        (g_tick, g_phase, _), = ev(self.rows, "gather_end")
        self.assertEqual(g_phase, "gather")
        self.assertIn((g_tick, "quan", 1), ev(self.rows, "phase_start"))
        (q_tick, q_phase, _), = ev(self.rows, "quan_end")
        self.assertEqual(q_phase, "quan")
        self.assertIn((q_tick, "shop", 1), ev(self.rows, "phase_start"))
        (s_tick, s_phase, s_day), = ev(self.rows, "shop_end")
        self.assertEqual((s_phase, s_day), ("shop", 1))
        self.assertIn((s_tick, "gather", 2), ev(self.rows, "day_start"))

    def test_next_day_hold_gets_new_ids_in_array_order(self):
        day2 = [r for r in self.rows if r["type"] == "snapshot" and r.get("day") == 2 and r["phase"] == "gather"]
        ids = [h["id"] for h in day2[0]["hold"]]
        kinds = [h["kind"] for h in day2[0]["hold"]]
        self.assertEqual(kinds, ["ca_loc", "bong_sung"])
        self.assertTrue(set(ids).isdisjoint({"I1", "I2"}), ids)


if __name__ == "__main__":
    unittest.main()
