"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]
        self._elapsed_ticks = 0
        self._next_customer_tick = int(t["first_customer_tick"]) if scenario.get("random_customers", True) else None
        self._reserve_fixture_customers()
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        available_stock = self._available_stock()
        return {
            "player": {"pos": self.pos},
            "stock": {k: available_stock[k] for k in sorted(available_stock) if available_stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._elapsed_ticks += 1

        # Kiên nhẫn bắt đầu giảm ở tick sau khi khách đến/được dựng fixture.
        for c in sort_by_id(self.customers):
            if c.get("state", "waiting") == "waiting" and c.get("arrived_tick", 0) != self._elapsed_ticks:
                c["patience_ticks_left"] = max(0, int(c.get("patience_ticks_left",
                                                              int(round(self.t["patience_s"] * TICK))) - 1))
        events.extend(self._remove_impatient_customers())

        self._move(inp)
        # TODO(nhóm): tối đa MỘT interact, chọn đối tượng theo (khoảng cách, bếp trước bàn, id).
        if not self.done and self._next_customer_tick is not None and self._elapsed_ticks >= self._next_customer_tick:
            events.extend(self._seat_scheduled_customer())
            interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
            self._next_customer_tick += max(1, interval_ticks)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.extend(self._close_customers())
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _reserve_fixture_customers(self):
        for c in self.customers:
            dish_id = c.get("dish_id")
            if dish_id is not None and dish_id not in self.menu:
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: dish_id không có trong menu")

            order_status = c.get("order_status", "reserved")
            if order_status not in ("reserved", "assigned", "unfulfillable", "served"):
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
            reserved = c.get("reserved")
            if reserved is None:
                reserved = {}
            if not isinstance(reserved, dict):
                from ..errors import BadInput
                raise BadInput(f"customers.{c['id']}: reserved phải là object")
            if dish_id is not None and order_status == "reserved" and not reserved:
                reserved = dict(self.menu[dish_id]["recipe"])
            if order_status != "reserved":
                reserved = {}

            for kind, qty in reserved.items():
                if kind not in self.stock or qty > self.stock.get(kind, 0):
                    from ..errors import BadInput
                    raise BadInput(f"customers.{c['id']}: reserved vượt kho khả dụng")

            c["reserved"] = reserved
            c["dish_id"] = dish_id
            c["order_tick"] = int(c.get("order_tick", 0))
            c["order_status"] = order_status
            c["state"] = c.get("state", "waiting")
            c["patience_ticks_left"] = int(c.get("patience_ticks_left",
                                                  int(round(self.t["patience_s"] * TICK))))
            c["eat_ticks_left"] = int(c.get("eat_ticks_left", 0))
            c["base_price"] = int(c.get("base_price", self.menu[dish_id]["price"] if dish_id else 0))
            c["tip"] = int(c.get("tip", 0))
            c["arrived_tick"] = 0

        totals = {}
        for c in self.customers:
            if c["order_status"] == "reserved":
                for kind, qty in c["reserved"].items():
                    totals[kind] = totals.get(kind, 0) + qty
        for kind, qty in totals.items():
            if qty > self.stock.get(kind, 0):
                from ..errors import BadInput
                raise BadInput(f"tổng reserved vượt kho khả dụng: {kind}")

    def _available_stock(self):
        reserved_totals = {}
        for c in self.customers:
            if c.get("order_status") == "reserved":
                for kind, qty in c.get("reserved", {}).items():
                    reserved_totals[kind] = reserved_totals.get(kind, 0) + qty
        return {
            kind: max(0, qty - reserved_totals.get(kind, 0))
            for kind, qty in self.stock.items()
        }

    def _available_dishes(self):
        available = []
        available_stock = self._available_stock()
        for dish_id in sorted(self.menu):
            recipe = self.menu[dish_id]["recipe"]
            if all(available_stock.get(kind, 0) >= qty for kind, qty in recipe.items()):
                available.append(dish_id)
        return available

    def _seat_scheduled_customer(self):
        empty_tables = [
            tb for tb in sort_by_id(self.tables)
            if not any(c.get("table_id") == tb["id"] for c in self.customers)
        ]
        if not empty_tables:
            return []

        available = self._available_dishes()
        if not available:
            return [("no_dish", {"reason": "no_dish"})]

        dish_id = self.rng.get("customers").choice(available)
        recipe = dict(self.menu[dish_id]["recipe"])
        table = empty_tables[0]
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "reserved": recipe,
            "order_tick": self._elapsed_ticks,
            "order_status": "reserved",
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "base_price": int(self.menu[dish_id]["price"]),
            "tip": 0,
            "arrived_tick": self._elapsed_ticks,
        }
        self.customers.append(customer)
        return [("customer_arrived", {
            "customer_id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
        })]

    def _release_reserved(self, customer):
        customer["reserved"] = {}

    def _remove_impatient_customers(self):
        events = []
        remaining = []
        for c in sort_by_id(self.customers):
            if c.get("state", "waiting") == "waiting" and c.get("patience_ticks_left", 0) <= 0:
                self._release_reserved(c)
                self.reputation = max(float(self.t["reputation_min"]),
                                      self.reputation + float(self.t["left_reputation_delta"]))
                events.append(("customer_left", {
                    "customer_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "patience",
                }))
            else:
                remaining.append(c)
        self.customers = remaining
        return events

    def _close_customers(self):
        events = []
        for c in sort_by_id(self.customers):
            self._release_reserved(c)
            events.append(("customer_left", {
                "customer_id": c["id"],
                "table_id": c["table_id"],
                "reason": "closing",
            }))
        self.customers = []
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
