"""Test Contract v1.1 mục 4.2: pause ở cả ba mode (gather, quan, day)."""

import unittest

from helpers import Workdir, read_jsonl, run_headless, write_json

# bước k đọc frame tick k; event của bước k có tick k+1
FRAMES = {"frames": [{"tick": 5, "pause": True}, {"tick": 6, "pause": False, "interact": True},
                     {"tick": 7, "interact": False}, {"tick": 10, "pause": True}, {"tick": 11, "pause": False}]}


def run(w, mode):
    write_json(w.path("in.json"), FRAMES)
    code, err = run_headless("--mode", mode, "--seed", "1", "--ticks", "20", "--inputs", w.path("in.json"),
                             "--snapshot-every", "1", "--out", w.path(f"{mode}.jsonl"))
    assert code == 0, err
    return read_jsonl(w.path(f"{mode}.jsonl"))


class PauseAllModes(unittest.TestCase):
    def check(self, mode):
        with Workdir() as w:
            rows = run(w, mode)
        ev = [(r["tick"], r["name"]) for r in rows if r["type"] == "event" and r["name"] in ("paused", "resumed")]
        self.assertEqual(ev, [(6, "paused"), (11, "resumed")], mode)
        snaps = {r["tick"]: r for r in rows if r["type"] == "snapshot"}
        for t in range(6, 11):
            self.assertEqual(snaps[t]["state"], "paused", (mode, t))
            self.assertEqual(snaps[t]["sim_tick"], 5, (mode, t))           # sim_tick đứng yên
            self.assertEqual(snaps[t]["phase_tick"], snaps[5]["phase_tick"], (mode, t))
            self.assertEqual(snaps[t]["time_left_ticks"], snaps[5]["time_left_ticks"], (mode, t))  # đồng hồ dừng
        self.assertEqual(snaps[11]["state"], "playing")
        self.assertEqual(snaps[11]["sim_tick"], 6)  # resumed chạy gameplay ngay trong bước đó
        self.assertEqual(rows[-1]["sim_tick"], 15)
        return rows

    def test_gather(self):
        rows = self.check("gather")
        # cạnh interact ở frame 6 rơi vào lúc pause -> bị bỏ qua, không cập bến
        self.assertFalse([r for r in rows if r["type"] == "event" and r["name"] == "gather_end"])

    def test_quan(self):
        self.check("quan")

    def test_day(self):
        self.check("day")


if __name__ == "__main__":
    unittest.main()
