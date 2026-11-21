"""Mở rộng `current` (Dòng nước lũ, TICKET-03 mục 2). Số liệu đọc từ game.contract.json."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

C = load_contract()
T = C["tuning"]
CUR = T["gather"]["current"]
EVERY, DUR, WARN = CUR["interval_ticks"], CUR["duration_ticks"], CUR["warning_ticks"]
IDLE = InputState((0.0, 0.0), {}, set())


def sim(pos=(50.0, 0.0), **extra):  # mặt nước: không hết oxy khi chạy dài
    sc = {"player": {"pos": list(pos)}, "random_fish": False, "monsters": [], "nodes": [], **extra}
    return GatherSim(T, sc, Streams(3), IdAllocator(), day=1)


def run_until(s, tick):
    """Chạy tới hết bước `tick` (phase_tick); trả {tick: [events]}."""
    out = {}
    while s.phase_tick < tick and not s.done:
        ev = s.step(IDLE)
        out[s.phase_tick] = ev
    return out


def names(ev):
    return [n for n, _ in ev]


class CurrentExt(unittest.TestCase):
    def test_manifest(self):
        self.assertIn("current", C["extensions"])
        self.assertEqual((EVERY, DUR, WARN, CUR["min_depth"], CUR["speed"]), (1800, 480, 120, 10, 1.5))

    def test_schedule_warning_start_end_exact_ticks(self):
        s = sim()
        log = run_until(s, EVERY + DUR)
        self.assertEqual([(t, n) for t, ev in log.items() for n in names(ev) if n.startswith("current")],
                         [(EVERY - WARN, "current_warning"), (EVERY, "current_start"), (EVERY + DUR, "current_end")])
        warn = dict(log[EVERY - WARN])["current_warning"]
        self.assertEqual(warn, {"starts_at_phase_tick": EVERY})
        start = dict(log[EVERY])["current_start"]
        self.assertIn(start["direction"], (-1, 1))
        self.assertEqual(start["duration_ticks"], DUR)
        self.assertEqual(dict(log[EVERY + DUR])["current_end"], {"direction": start["direction"], "reason": "elapsed"})

    def test_snapshot_ticks_left_counts_captured_tick(self):
        s = sim(current_direction=1)
        run_until(s, EVERY)
        self.assertEqual(s.snapshot()["current"], {"direction": 1, "ticks_left": DUR})
        run_until(s, EVERY + DUR - 1)
        self.assertEqual(s.snapshot()["current"], {"direction": 1, "ticks_left": 1})
        run_until(s, EVERY + DUR)
        self.assertIsNone(s.snapshot()["current"])

    def test_force_only_when_deep_and_vel_untouched(self):
        for d, moved in ((CUR["min_depth"] + 2, True), (CUR["min_depth"] - 2, False)):
            s = sim(pos=(50.0, d), current_direction=-1)
            s.phase_tick = EVERY - 1  # nhảy tới ngay trước bước bắt đầu dòng
            s.step(IDLE)
            dx = s.pos[0] - 50.0
            self.assertAlmostEqual(dx, -CUR["speed"] / 60 if moved else 0.0)
            self.assertEqual(s.vel, [0.0, 0.0])

    def test_phase_end_while_active_emits_phase_end_before_gather_end(self):
        s = sim(pos=(50.0, 12.0), current_direction=1, time_left_ticks=1)
        s.phase_tick = EVERY - 1
        ev = names(s.step(IDLE))  # bước bắt đầu dòng trùng bước cuối ca
        self.assertLess(ev.index("current_start"), ev.index("current_end"))
        self.assertEqual(ev.index("current_end") + 1, ev.index("gather_end"))
        self.assertAlmostEqual(s.pos[0], 50.0 + CUR["speed"] / 60)  # vẫn có lực

    def test_random_current_false_disables(self):
        s = sim(random_current=False)
        log = run_until(s, EVERY + 10)
        self.assertFalse(any(n.startswith("current") for ev in log.values() for n in names(ev)))
        self.assertNotIn("current", s.snapshot())

    def test_direction_deterministic_by_seed(self):
        dirs = []
        for _ in range(2):
            s = sim()
            log = run_until(s, EVERY)
            dirs.append(dict(log[EVERY])["current_start"]["direction"])
        self.assertEqual(dirs[0], dirs[1])


if __name__ == "__main__":
    unittest.main()
