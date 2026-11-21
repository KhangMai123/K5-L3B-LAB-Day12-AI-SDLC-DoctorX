"""TICKET-03: giá theo độ tươi, giữ lại khi hàng vừa ươn, schema kho v1.2 sai → mã 2."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session

from helpers import Workdir, run_headless, write_json

T = load_contract()["tuning"]
Q, MENU = T["quan"], T["menu"]
STOVE, TABLE = Q["stoves"][0], Q["tables"][0]
DISH = "ca_loc_nuong_trui"
IDLE = InputState((0.0, 0.0), {}, set())
PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})


def quan(stock, reserved, **kw):
    c = {"id": "C1", "table_id": TABLE["id"], "dish_id": DISH, "reserved": reserved}
    return Session("quan", T, {"random_customers": False, "stock": stock, "customers": [c], **kw}, 1)


class FreshRules(unittest.TestCase):
    def test_base_price_floor_of_list_price_times_avg_fresh(self):
        s = quan([{"id": "I1", "kind": "ca_loc", "fresh": 50.0}], ["I1"], player={"pos": STOVE["pos"]})
        ev = s.step(PRESS)
        cook = [e for e in ev if e["name"] == "cook_started"][0]["data"]
        # hao tươi kho quán xảy ra trước tương tác trong cùng bước -> fresh hơi dưới 50
        used = cook["items"][0]["fresh"]
        self.assertLess(used, 50.0)
        self.assertEqual(cook["base_price"], math.floor(MENU[DISH]["price"] * used / 100))
        self.assertEqual(cook["base_price"], 29)

    def test_reserved_item_just_spoiled_is_released_and_rereserved_once(self):
        stock = [{"id": "I1", "kind": "ca_loc", "fresh": 30.0}, {"id": "I2", "kind": "ca_loc", "fresh": 80.0}]
        s = quan(stock, ["I1"])
        names = [e["name"] for e in s.step(IDLE)]
        self.assertIn("spoiled", names)
        c = s.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_reserved_item_spoiled_without_replacement_becomes_unfulfillable(self):
        s = quan([{"id": "I1", "kind": "ca_loc", "fresh": 30.0}], ["I1"])
        s.step(IDLE)
        c = s.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("unfulfillable", []))
        self.assertEqual(c["state"], "waiting")  # khách vẫn chờ tới hết kiên nhẫn

    def test_v12_inventory_bad_schemas_exit_2(self):
        bad = [
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 90}, {"id": "I1", "kind": "ca_loc", "fresh": 80}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100.5}]},
            {"items": [{"id": "I1", "kind": "ca_loc", "fresh": -1}]},
            {"items": [{"id": "I1", "kind": "ca_ho", "fresh": 90}]},
            {"items": [{"id": "", "kind": "ca_loc", "fresh": 90}]},
            {"items": {"ca_loc": 1}},
        ]
        with Workdir() as w:
            for i, inv in enumerate(bad):
                p = w.path(f"b{i}.json")
                write_json(p, inv)
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", p,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, inv)
            write_json(w.path("ok.json"), {"items": []})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", w.path("ok.json"),
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
