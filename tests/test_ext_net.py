"""Mở rộng `net` (Vợt hút cá, TICKET-02 mục 3). Số liệu đọc từ game.contract.json."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.day import ShopSim
from chonoi.sim.gather import GatherSim

C = load_contract()
T = C["tuning"]
NET = {r["level"]: r for r in T["shop"]["upgrades"]["net"]}
Y = T["gather"]["fish_yield"]
POS = [50.0, 15.0]


def catch():
    return InputState((0.0, 0.0), {"catch": True}, {"catch"})


def sim(level, fish, hold=None):
    sc = {"player": {"pos": POS}, "random_fish": False, "monsters": [], "nodes": [], "fish": fish}
    if hold is not None:
        sc["hold"] = hold
    return GatherSim(T, sc, Streams(1), IdAllocator(), day=1, active_upgrades={"net": level} if level else {})


def school(i, kind, dx):
    return {"id": f"F{i}", "kind": kind, "pos": [POS[0] + dx, POS[1]]}


def caught(events):
    return [d["fish_id"] for n, d in events if n == "fish_caught"]


class NetExt(unittest.TestCase):
    def test_manifest_declares_net(self):
        self.assertIn("net", C["extensions"])
        self.assertEqual((NET[1]["price"], NET[1]["catch_radius"], NET[1]["max_schools"]), (250, 4.0, 2))
        self.assertEqual((NET[2]["price"], NET[2]["catch_radius"], NET[2]["max_schools"]), (500, 6.0, 3))

    def test_level0_keeps_core_nearest_only(self):
        s = sim(0, [school(1, "ca_loc", 1.0), school(2, "ca_loc", 1.5)])
        self.assertEqual(caught(s.step(catch())), ["F1"])

    def test_level1_catches_up_to_two_by_id_within_4m(self):
        # F3 gần nhất nhưng id lớn -> duyệt theo id: F1, F2 rồi dừng ở trần 2 đàn
        s = sim(1, [school(1, "ca_loc", 3.5), school(2, "ca_loc", 3.0), school(3, "ca_loc", 0.5),
                    school(4, "ca_loc", 4.5)])
        self.assertEqual(caught(s.step(catch())), ["F1", "F2"])
        self.assertGreater(s.catch_cd_ticks, 0)

    def test_level2_radius_6_and_three_schools(self):
        s = sim(2, [school(1, "ca_loc", 5.5), school(2, "ca_loc", -5.0), school(3, "ca_loc", 1.0),
                    school(4, "ca_loc", 2.0)])
        self.assertEqual(caught(s.step(catch())), ["F1", "F2", "F3"])

    def test_school_without_room_emits_hold_full_and_next_is_tried(self):
        cap = T["gather"]["hold_capacity"]
        free = Y["ca_linh"] - 1  # thiếu 1 chỗ cho cá linh, đủ cho cá lóc
        hold = [{"id": f"I{i}", "kind": "bong_sung", "fresh": 100} for i in range(1, cap - free + 1)]
        s = sim(1, [school(1, "ca_linh", 1.0), school(2, "ca_loc", 1.5)], hold=hold)
        ev = s.step(catch())
        self.assertEqual([n for n, _ in ev if n in ("hold_full", "fish_caught")], ["hold_full", "fish_caught"])
        self.assertEqual(caught(ev), ["F2"])
        self.assertEqual([f["id"] for f in s.fish], ["F1"])  # đàn thiếu chỗ được giữ lại

    def test_no_success_no_cooldown(self):
        cap = T["gather"]["hold_capacity"]
        hold = [{"id": f"I{i}", "kind": "bong_sung", "fresh": 100} for i in range(1, cap + 1)]
        s = sim(1, [school(1, "ca_loc", 1.0)], hold=hold)
        ev = s.step(catch())
        self.assertEqual([n for n, _ in ev], ["hold_full"])
        self.assertEqual(s.catch_cd_ticks, 0)

    def test_shop_buys_net_levels_then_max_level(self):
        shop = ShopSim(T, 800, 800, 3.0, {}, [], Streams(1))
        buy = lambda: shop.step(InputState((0.0, 0.0), {}, set(), buy="net"))
        self.assertEqual(buy(), [("bought", {"upgrade": "net", "level": 1, "price": 250, "money": 550})])
        self.assertEqual(buy(), [("bought", {"upgrade": "net", "level": 2, "price": 500, "money": 50})])
        ev = buy()
        self.assertEqual((ev[0][0], ev[0][1]["reason"]), ("buy_failed", "max_level"))
        self.assertEqual(shop.money, 50)


if __name__ == "__main__":
    unittest.main()
