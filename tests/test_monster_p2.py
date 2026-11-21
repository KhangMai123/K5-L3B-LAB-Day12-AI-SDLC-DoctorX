"""TICKET-02 mục 1.2: Cá Sấu — M2 từ Ngày 3, hit/bỏ hàng LIFO, recoil 60 bước lùi XA người chơi."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim

T = load_contract()["tuning"]
SP = T["gather"]["monsters"]["species"]["ca_sau"]
IDLE = InputState((0.0, 0.0), {}, set())


def sim(monster_pos, player=(50.0, 15.0), hold=(), day=1):
    m = {"id": "M1", "kind": "ca_sau", "pos": list(monster_pos),
         "waypoints": [list(monster_pos), [monster_pos[0] + 4, monster_pos[1]]]}
    sc = {"player": {"pos": list(player)}, "random_fish": False, "nodes": [], "monsters": [m],
          "hold": [{"id": f"I{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(hold)]}
    return GatherSim(T, sc, Streams(1), IdAllocator(), day=day)


class MonsterP2(unittest.TestCase):
    def test_m2_only_from_day_3(self):
        def ids(day):
            sc = {"random_fish": False}
            return [m["id"] for m in GatherSim(T, sc, Streams(1), IdAllocator(), day=day).monsters]
        self.assertEqual((ids(1), ids(2), ids(3)), (["M1"], ["M1"], ["M1", "M2"]))

    def test_hit_drops_floor_half_lifo_and_sets_invuln(self):
        s = sim((50.5, 15.0), hold=("ca_loc", "bong_sung", "ca_linh"))
        ev = dict(s.step(IDLE))
        hit = ev["monster_hit"]
        self.assertEqual(hit["hp"], T["gather"]["hp_max"] - 1)
        self.assertEqual([x["id"] for x in hit["lost"]], ["I3"])  # floor(3/2)=1, mới nhất trước
        self.assertEqual(s.invuln_ticks, T["gather"]["monsters"]["invuln_ticks"])

    def test_recoil_moves_away_from_player_for_recoil_ticks(self):
        s = sim((51.0, 15.0))  # quái ở bên phải người chơi -> lùi về +x
        s.step(IDLE)
        m = s.monsters[0]
        self.assertEqual(m["state"], "recoil")
        self.assertEqual(m["recoil_dir"], [1.0, 0.0])
        x0 = m["pos"][0]
        s.step(IDLE)  # recoil bắt đầu từ bước sau
        self.assertAlmostEqual(m["pos"][0] - x0, SP["recoil_dist"] / SP["recoil_ticks"])
        for _ in range(SP["recoil_ticks"] - 1):
            s.step(IDLE)
        self.assertEqual(m["state"], "patrol")
        self.assertAlmostEqual(m["pos"][0] - x0, SP["recoil_dist"], places=6)

    def test_coincident_centers_recoil_plus_x(self):
        s = sim((50.0, 15.0))
        s.step(IDLE)
        self.assertEqual(s.monsters[0]["recoil_dir"], [1.0, 0.0])


if __name__ == "__main__":
    unittest.main()
