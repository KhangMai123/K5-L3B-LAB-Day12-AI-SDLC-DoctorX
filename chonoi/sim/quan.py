"""Buổi tối — Mở Quán (Phase 1 lõi đã xong).

Lát 3: khách theo lịch, chọn món đủ kho, giữ chỗ, kiên nhẫn, customer_left, no_dish.
Lát 4: interact bếp/bàn (cook_started, dish_ready, dish_picked, served), paid, boa, uy tín, quan_end.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0
FRESH_UNITS = 240
QUAN_DECAY_UNITS = 1  # 0.25/s


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, money=0, earned=0,
                 reputation=None, menu_filter=None):
        t = tuning["quan"]
        self.t = t
        self.fresh_cfg = tuning["freshness"]
        full_menu = tuning["menu"]
        if menu_filter:
            self.menu = {k: full_menu[k] for k in menu_filter if k in full_menu}
        else:
            self.menu = full_menu
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        raw = inventory if inventory is not None else scenario.get("stock", [])
        self.stock = self._parse_stock(raw, ids)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", reputation if reputation is not None else t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = [dict(c) for c in scenario.get("customers", [])]
        self._elapsed_ticks = 0
        self._next_customer_tick = int(t["first_customer_tick"]) if scenario.get("random_customers", True) else None
        self._reserve_fixture_customers()
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = int(money)
        self.earned = int(earned)
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _parse_stock(self, raw, ids):
        initial = float(self.fresh_cfg["initial"])
        out = []
        if isinstance(raw, dict):
            # tương thích fixture đếm cũ → cấp cá thể fresh=100
            for kind in sorted(raw):
                for _ in range(int(raw[kind])):
                    out.append({
                        "id": ids.new("I"), "kind": kind, "fresh": initial,
                        "_units": int(round(initial * FRESH_UNITS)),
                    })
            return out
        for it in raw or []:
            if isinstance(it, str):
                out.append({
                    "id": ids.new("I"), "kind": it, "fresh": initial,
                    "_units": int(round(initial * FRESH_UNITS)),
                })
            else:
                fresh = float(it.get("fresh", initial))
                iid = it.get("id") or ids.new("I")
                if "id" in it:
                    ids.reserve(it["id"])
                out.append({
                    "id": iid, "kind": it["kind"], "fresh": fresh,
                    "_units": int(round(fresh * FRESH_UNITS)),
                })
        return out

    def _spoiled_below(self):
        return float(self.fresh_cfg["spoiled_below"])

    def _item_by_id(self, iid):
        for it in self.stock:
            if it["id"] == iid:
                return it
        return None

    def _reserved_ids(self):
        ids = set()
        for c in self.customers:
            if c.get("order_status") == "reserved":
                for iid in c.get("reserved", []):
                    ids.add(iid if isinstance(iid, str) else iid.get("id"))
        return ids

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
        custs = []
        for c in sort_by_id(self.customers):
            cc = dict(c)
            cc["reserved"] = list(c.get("reserved", []))
            custs.append(cc)
        return {
            "player": {"pos": self.pos},
            "stock": [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
                      for it in sorted(self.stock, key=lambda x: x["id"])],
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": custs,
        }

    def _decay_stock(self, events):
        thr = self._spoiled_below()
        spoiled = []
        for it in self.stock:
            before = it["fresh"]
            it["_units"] = max(0, it["_units"] - QUAN_DECAY_UNITS)
            it["fresh"] = it["_units"] / FRESH_UNITS
            if before >= thr and it["fresh"] < thr:
                spoiled.append(it)
        for it in sorted(spoiled, key=lambda x: x["id"]):
            events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        # giữ chỗ bị ươn → nhả và thử giữ lại
        if spoiled:
            spoiled_ids = {it["id"] for it in spoiled}
            affected = []
            for c in self.customers:
                if c.get("order_status") != "reserved":
                    continue
                if any(iid in spoiled_ids for iid in c.get("reserved", [])):
                    c["reserved"] = []
                    affected.append(c)
            for c in sorted(affected, key=lambda x: (x["order_tick"], id_key(x["table_id"]))):
                ids = self._pick_reserve_ids(c["dish_id"])
                if ids is None:
                    c["order_status"] = "unfulfillable"
                    c["reserved"] = []
                else:
                    c["reserved"] = ids
                    c["order_status"] = "reserved"

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._elapsed_ticks += 1
        self._decay_stock(events)

        for c in self.customers:
            timer = "eat_ticks_left" if c["state"] == "eating" else "patience_ticks_left"
            c[timer] = max(0, c[timer] - 1)
        events.extend(self._tick_stoves())  # nấu / chín / cháy trước di chuyển

        self._move(inp)
        if inp.pressed("interact"):
            events.extend(self._interact())

        closing = self.time_left_ticks == 0
        events.extend(self._settle_customers(closing))
        self._cancel_orphan_orders()
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        elif self._next_customer_tick is not None and self._elapsed_ticks >= self._next_customer_tick:
            events.extend(self._seat_scheduled_customer())
            interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
            self._next_customer_tick += max(1, interval_ticks)
        return events

    def _usable_items(self, exclude_ids=None):
        exclude_ids = exclude_ids or set()
        reserved = self._reserved_ids() | exclude_ids
        thr = self._spoiled_below()
        return [it for it in self.stock if it["id"] not in reserved and it["fresh"] >= thr]

    def _pick_reserve_ids(self, dish_id, exclude_ids=None):
        """Chọn cá thể tươi nhất theo kind rồi id. Trả list id hoặc None."""
        recipe = self.menu[dish_id]["recipe"]
        pool = list(self._usable_items(exclude_ids))
        chosen = []
        used = set()
        for kind, qty in sorted(recipe.items()):
            cands = sorted(
                [it for it in pool if it["kind"] == kind and it["id"] not in used],
                key=lambda it: (-it["fresh"], it["id"]),
            )
            if len(cands) < qty:
                return None
            for it in cands[:qty]:
                chosen.append(it["id"])
                used.add(it["id"])
        return chosen

    def _reserve_fixture_customers(self):
        from ..errors import BadInput
        for c in sorted(self.customers, key=lambda x: (int(x.get("order_tick", 0)), id_key(x.get("table_id", "")))):
            dish_id = c.get("dish_id")
            if dish_id is not None and dish_id not in self.menu:
                raise BadInput(f"customers.{c['id']}: dish_id không có trong menu")

            order_status = c.get("order_status", "reserved")
            if order_status not in ("reserved", "assigned", "unfulfillable", "served"):
                raise BadInput(f"customers.{c['id']}: order_status không hợp lệ")
            reserved = c.get("reserved")
            if order_status != "reserved":
                reserved = []
            elif reserved in (None, {}):
                reserved = self._pick_reserve_ids(dish_id)
                if reserved is None:
                    raise BadInput(f"customers.{c['id']}: không đủ nguyên liệu tươi để giữ chỗ")
            elif isinstance(reserved, dict):
                # fixture đếm cũ
                reserved = self._pick_reserve_ids(dish_id)
                if reserved is None:
                    raise BadInput(f"customers.{c['id']}: reserved vượt kho khả dụng")
            elif isinstance(reserved, list):
                ids = []
                for r in reserved:
                    iid = r if isinstance(r, str) else r.get("id")
                    if self._item_by_id(iid) is None:
                        raise BadInput(f"customers.{c['id']}: reserved id không tồn tại")
                    ids.append(iid)
                reserved = ids
            else:
                raise BadInput(f"customers.{c['id']}: reserved không hợp lệ")

            c["reserved"] = reserved or []
            c["dish_id"] = dish_id
            c["order_tick"] = int(c.get("order_tick", 0))
            c["order_status"] = order_status
            c["state"] = c.get("state", "waiting")
            c["patience_ticks_left"] = int(c.get("patience_ticks_left",
                                                  int(round(self.t["patience_s"] * TICK))))
            c["eat_ticks_left"] = int(c.get("eat_ticks_left", 0))
            c["base_price"] = int(c.get("base_price", self.menu[dish_id]["price"] if dish_id else 0))
            c["tip"] = int(c.get("tip", 0))

    def _available_stock(self):
        counts = {}
        for it in self._usable_items():
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
        return counts

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
            return [("no_dish", {})]

        dish_id = self.rng.get("customers").choice(available)
        reserved = self._pick_reserve_ids(dish_id)
        table = empty_tables[0]
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
            "reserved": reserved,
            "order_tick": self._elapsed_ticks,
            "order_status": "reserved",
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "base_price": int(self.menu[dish_id]["price"]),
            "tip": 0,
        }
        self.customers.append(customer)
        return [("customer_arrived", {
            "order_id": customer_id,
            "table_id": table["id"],
            "dish_id": dish_id,
        })]

    def _settle_customers(self, closing):
        events = []
        remaining = []
        for c in sorted(self.customers, key=lambda customer: id_key(customer["table_id"])):
            if c["state"] == "eating":
                if closing or c["eat_ticks_left"] == 0:
                    events.append(self._pay(c, "closing" if closing else "finished_eating"))
                else:
                    remaining.append(c)
            elif closing or c["patience_ticks_left"] == 0:
                if not closing:
                    self._rep(float(self.t["left_reputation_delta"]))
                events.append(("customer_left", {
                    "order_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "closing" if closing else "patience",
                    "reputation": self.reputation,
                }))
            else:
                remaining.append(c)
        self.customers = remaining
        return events

    # --- Lát 4: bếp, bưng, phục vụ, tiền, uy tín ------------------------------
    def _ticks(self, seconds):
        return int(round(seconds * TICK))

    def _customer(self, customer_id):
        for c in self.customers:
            if c["id"] == customer_id:
                return c
        return None

    def _rep(self, delta):
        lo, hi = float(self.t["reputation_min"]), float(self.t["reputation_max"])
        self.reputation = min(hi, max(lo, self.reputation + delta))

    def _cancel_orphan_orders(self):
        """Khách đã bỏ đi -> hủy món đang nấu/chín/trên tay; không hoàn nguyên liệu (clarify #4)."""
        for s in self.stoves:
            if s["dish"] is not None and self._customer(s["dish"]["order_id"]) is None:
                s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self._customer(self.hand["order_id"]) is None:
            self.hand = None

    def _tick_stoves(self):
        events = []
        burn_s = self.t.get("burn_s")
        burn_ticks = int(round(burn_s * TICK)) if burn_s is not None else None
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                # chỉ tăng ready_ticks cho món đã ready ở đầu bước — đã ready trước khi vào đây
                prev_ready = s["ready_ticks"]
                s["ready_ticks"] = prev_ready + 1
                if burn_ticks is not None and s["ready_ticks"] > burn_ticks:
                    order_id = s["dish"]["order_id"]
                    dish_id = s["dish"]["dish_id"]
                    c = self._customer(order_id)
                    s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
                    order_status = "unfulfillable"
                    if c is not None and c.get("state") == "waiting":
                        ids = self._pick_reserve_ids(dish_id)
                        if ids is not None:
                            c["reserved"] = ids
                            c["order_status"] = "reserved"
                            order_status = "reserved"
                        else:
                            c["reserved"] = []
                            c["order_status"] = "unfulfillable"
                            order_status = "unfulfillable"
                    events.append(("dish_burnt", {
                        "stove_id": s["id"], "order_id": order_id, "dish_id": dish_id,
                        "order_status": order_status,
                    }))
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"], s["ready_ticks"] = "ready", 0
                    events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                                  "dish_id": s["dish"]["dish_id"]}))
        return events

    def _interact(self):
        """Tối đa MỘT interact: đối tượng gần nhất trong interact_radius, hòa -> bếp trước bàn -> id."""
        r = self.t["interact_radius"]
        cands = [(math.dist(self.pos, o["pos"]), kind, id_key(o["id"]), o)
                 for kind, coll in ((0, self.stoves), (1, self.tables)) for o in coll]
        cands = [c for c in cands if c[0] <= r]
        if not cands:
            return []
        _, kind, _, target = min(cands, key=lambda c: c[:3])
        if kind == 0:
            if target["state"] == "idle":
                return self._cook(target)
            if target["state"] == "ready":
                return self._pick(target)
            return []
        return self._serve(target)

    def _cook(self, stove):
        orders = [c for c in self.customers if c.get("order_status") == "reserved" and c.get("dish_id")]
        if not orders:
            return []
        c = min(orders, key=lambda order: (order["order_tick"], id_key(order["table_id"])))
        dish_id = c["dish_id"]
        used = []
        for iid in c["reserved"]:
            it = self._item_by_id(iid)
            if it is None:
                return []
            used.append(it)
        if not used:
            return []
        avg_fresh = sum(it["fresh"] for it in used) / len(used)
        list_price = int(self.menu[dish_id]["price"])
        base_price = int(math.floor(list_price * avg_fresh / 100.0))
        c["base_price"] = base_price
        items = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
                 for it in sorted(used, key=lambda x: (x["kind"], x["id"]))]
        for it in used:
            self.stock.remove(it)
        c["reserved"], c["order_status"] = [], "assigned"
        stove.update(state="cooking", dish={"dish_id": dish_id, "order_id": c["id"], "base_price": base_price},
                     cook_ticks_left=max(1, self._ticks(self.menu[dish_id]["cook_s"])), ready_ticks=0)
        return [("cook_started", {"stove_id": stove["id"], "order_id": c["id"], "dish_id": dish_id,
                                  "items": items, "base_price": base_price})]

    def _pick(self, stove):
        if self.hand is not None:  # carry_limit = 1
            return []
        dish = stove["dish"]
        self.hand = dish
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        return [("dish_picked", {"stove_id": stove["id"], "order_id": dish["order_id"],
                                 "dish_id": dish["dish_id"]})]

    def _serve(self, table):
        if self.hand is None:
            return []
        c = next((x for x in self.customers if x.get("table_id") == table["id"]), None)
        if c is None or c.get("state") != "waiting" or c["id"] != self.hand["order_id"]:
            return []
        price = int(self.hand["base_price"])
        full = self._ticks(self.t["patience_s"])
        ratio = c["patience_ticks_left"] / full if full > 0 else 0
        tip = math.floor(price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        c.update(state="eating", order_status="served", base_price=price, tip=tip,
                 eat_ticks_left=max(1, self._ticks(self.t["eat_s"])))
        self.hand = None
        return [("served", {"order_id": c["id"], "table_id": c["table_id"], "dish_id": c["dish_id"],
                            "patience_ticks_left": c["patience_ticks_left"], "base_price": price, "tip": tip})]

    def _pay(self, c, reason):
        base_price, tip = int(c["base_price"]), int(c["tip"])
        amount = base_price + tip
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if tip > 0:
            self._rep(float(self.t["tip_reputation"]))
        return ("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": base_price,
                         "tip": tip, "amount": amount, "reason": reason})

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
