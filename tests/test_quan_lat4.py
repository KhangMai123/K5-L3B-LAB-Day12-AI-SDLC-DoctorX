"""Lát 4 (Diệp): bếp, bưng, phục vụ, tiền, uy tín. Số liệu đọc từ game.contract.json, không hard-code."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session
from helpers import cook_item_kinds, stock_counts

T = load_contract()["tuning"]
Q, MENU = T["quan"], T["menu"]
STOVE, TABLE = Q["stoves"][0], Q["tables"][0]
OTHER_TABLE = dict(TABLE, id="T2")
TWO_TABLES = dict(T, quan=dict(Q, tables=[TABLE, OTHER_TABLE]))
DISH = "ca_loc_nuong_trui"
PRICE = MENU[DISH]["price"]
COOK = round(MENU[DISH]["cook_s"] * 60)
EAT = round(Q["eat_s"] * 60)
PATIENCE = round(Q["patience_s"] * 60)


def idle():
    return InputState((0.0, 0.0), {}, set())


def press(move=(0.0, 0.0)):
    return InputState(move, {"interact": True}, {"interact"})


def names(rows):
    return [r["name"] for r in rows]


def quan(tuning=T, **block):
    block.setdefault("random_customers", False)
    return Session("quan", tuning, block, 1)


def waiting_customer(**kw):
    c = {"id": "C1", "table_id": TABLE["id"], "dish_id": DISH}
    c.update(kw)
    return c


class Lat4(unittest.TestCase):
    def test_cook_takes_oldest_reserved_and_consumes_stock(self):
        s = quan(stock={"ca_loc": 2}, player={"pos": STOVE["pos"]},
                 tables=[], customers=[waiting_customer()])
        rows = s.step(press())
        self.assertEqual(names(rows), ["cook_started"])
        data = rows[0]["data"]
        self.assertEqual(data["stove_id"], STOVE["id"])
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["dish_id"], DISH)
        self.assertEqual(cook_item_kinds(data["items"]), ["ca_loc"])
        bp = data["base_price"]
        self.assertEqual(bp, int(math.floor(PRICE * data["items"][0]["fresh"] / 100)))
        snap = s.snapshot()
        st = snap["stoves"][0]
        self.assertEqual(st["state"], "cooking")
        self.assertEqual(st["dish"], {"dish_id": DISH, "order_id": "C1", "base_price": bp})
        self.assertEqual(st["cook_ticks_left"], COOK)
        c = snap["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("assigned", []))
        self.assertEqual(stock_counts(snap["stock"]), {"ca_loc": 1})

    def test_cook_breaks_order_tick_tie_by_table_id(self):
        s = quan(TWO_TABLES, stock={"ca_loc": 2}, player={"pos": STOVE["pos"]},
                 customers=[waiting_customer(table_id=OTHER_TABLE["id"]),
                            waiting_customer(id="C2")])
        self.assertEqual(s.step(press())[0]["data"]["order_id"], "C2")

    def test_stove_idle_without_order_does_nothing(self):
        s = quan(stock={"ca_loc": 1}, player={"pos": STOVE["pos"]})
        self.assertEqual(s.step(press()), [])
        self.assertEqual(s.snapshot()["stoves"][0]["state"], "idle")

    def test_dish_ready_exactly_after_cook_ticks(self):
        s = quan(stock={"ca_loc": 1}, player={"pos": STOVE["pos"]}, customers=[waiting_customer()])
        s.step(press())  # tick 1: cook_started
        for _ in range(COOK - 1):
            self.assertNotIn("dish_ready", names(s.step(idle())))
        rows = s.step(idle())
        self.assertEqual(rows[0]["name"], "dish_ready")
        self.assertEqual(rows[0]["tick"], 1 + COOK)
        self.assertEqual(rows[0]["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})
        self.assertEqual(s.snapshot()["stoves"][0]["state"], "ready")

    def test_pick_respects_carry_limit(self):
        stove = {"id": STOVE["id"], "state": "ready",
                 "dish": {"dish_id": DISH, "order_id": "C1", "base_price": PRICE}}
        s = quan(player={"pos": STOVE["pos"]}, stoves=[stove],
                 customers=[waiting_customer(order_status="assigned")])
        rows = s.step(press())
        self.assertEqual(names(rows), ["dish_picked"])
        self.assertEqual(rows[0]["data"], {"stove_id": STOVE["id"], "order_id": "C1", "dish_id": DISH})
        self.assertEqual(s.snapshot()["hand"], {"order_id": "C1", "dish_id": DISH, "base_price": PRICE})
        self.assertEqual(s.snapshot()["stoves"][0]["state"], "idle")
        # tay đã cầm món -> bếp chín thứ hai không bưng được
        s2 = quan(TWO_TABLES, player={"pos": STOVE["pos"]}, stoves=[stove],
                  hand={"order_id": "C2", "dish_id": DISH, "base_price": PRICE},
                  customers=[waiting_customer(order_status="assigned"),
                             waiting_customer(id="C2", table_id=OTHER_TABLE["id"], order_status="assigned")])
        self.assertEqual(s2.step(press()), [])

    def test_serve_with_tip_then_pay(self):
        s = quan(player={"pos": TABLE["pos"]}, hand={"order_id": "C1", "dish_id": DISH, "base_price": PRICE},
                 customers=[waiting_customer(order_status="assigned")])
        rows = s.step(press())
        tip = math.floor(PRICE * Q["tip_rate"])
        self.assertEqual(names(rows), ["served"])
        self.assertEqual(rows[0]["data"], {"order_id": "C1", "table_id": TABLE["id"], "dish_id": DISH,
                                          "patience_ticks_left": PATIENCE - 1, "base_price": PRICE, "tip": tip})
        snap = s.snapshot()
        self.assertIsNone(snap["hand"])
        self.assertEqual(snap["customers"][0]["state"], "eating")
        for _ in range(EAT - 1):
            self.assertEqual(s.step(idle()), [])
        rows = s.step(idle())
        self.assertEqual(names(rows), ["paid"])
        rep = min(Q["reputation_max"], Q["reputation_initial"] + Q["tip_reputation"])
        self.assertEqual(rows[0]["data"], {"order_id": "C1", "table_id": TABLE["id"], "base_price": PRICE,
                                          "tip": tip, "amount": PRICE + tip, "reason": "finished_eating"})
        snap = s.snapshot()
        self.assertEqual((snap["money"], snap["earned"], snap["customers"]), (PRICE + tip, PRICE + tip, []))
        self.assertEqual(snap["reputation"], rep)
        self.assertIsNone(snap["tables"][0]["customer_id"])

    def test_no_tip_below_patience_ratio(self):
        low = int(PATIENCE * Q["tip_min_patience_ratio"]) - 2
        s = quan(player={"pos": TABLE["pos"]}, hand={"order_id": "C1", "dish_id": DISH, "base_price": PRICE},
                 customers=[waiting_customer(order_status="assigned", patience_ticks_left=low)])
        self.assertEqual(s.step(press())[0]["data"]["tip"], 0)

    def test_serve_wrong_customer_does_nothing(self):
        s = quan(player={"pos": TABLE["pos"]}, hand={"order_id": "C9", "dish_id": DISH, "base_price": PRICE},
                 customers=[waiting_customer(order_status="assigned")])
        self.assertEqual(s.step(press()), [])

    def test_reputation_clamped_at_max(self):
        s = quan(reputation=Q["reputation_max"],
                 customers=[waiting_customer(state="eating", order_status="served", base_price=PRICE,
                                             tip=1, eat_ticks_left=1)])
        rows = s.step(idle())
        self.assertEqual(names(rows), ["paid"])
        self.assertEqual(s.snapshot()["reputation"], Q["reputation_max"])

    def test_customer_left_cancels_dish_on_stove(self):
        stove = {"id": STOVE["id"], "state": "cooking",
                 "dish": {"dish_id": DISH, "order_id": "C1", "base_price": PRICE},
                 "cook_ticks_left": 100}
        s = quan(stoves=[stove], customers=[waiting_customer(order_status="assigned", patience_ticks_left=1)])
        rows = s.step(idle())
        left = [r["data"] for r in rows if r["name"] == "customer_left"]
        self.assertEqual(left, [{"order_id": "C1", "table_id": TABLE["id"], "reason": "patience",
                                 "reputation": Q["reputation_initial"] + Q["left_reputation_delta"]}])
        st = s.snapshot()["stoves"][0]
        self.assertEqual((st["state"], st["dish"]), ("idle", None))

    def test_full_cycle_walk_cook_carry_serve_pay(self):
        s = quan(stock={"ca_loc": 1}, player={"pos": STOVE["pos"]}, customers=[waiting_customer()])
        seen = names(s.step(press()))
        for _ in range(COOK):
            seen += names(s.step(idle()))
        seen += names(s.step(press()))
        for _ in range(600):  # đi tới bàn
            p = s.snapshot()["player"]["pos"]
            dx, dz = TABLE["pos"][0] - p[0], TABLE["pos"][1] - p[1]
            if math.hypot(dx, dz) <= Q["interact_radius"] * 0.5:
                break
            n = math.hypot(dx, dz)
            seen += names(s.step(InputState((dx / n, dz / n), {}, set())))
        for _ in range(Q["ramp_max_ticks"] + 2):  # dừng hẳn
            seen += names(s.step(idle()))
        seen += names(s.step(press()))
        for _ in range(EAT):
            seen += names(s.step(idle()))
        self.assertEqual(seen, ["cook_started", "dish_ready", "dish_picked", "served", "paid"])
        self.assertGreaterEqual(s.snapshot()["money"], PRICE)


if __name__ == "__main__":
    unittest.main()
