"""Vòng Ngày (Phase 2): gather → quan → shop, lặp theo --days."""

import math

from .gather import GatherSim
from .quan import QuanSim

TICK = 60.0


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, money, earned, reputation, upgrades, stock, streams):
        self.t = tuning["shop"]
        self.tuning = tuning
        self.money = int(money)
        self.earned = int(earned)
        self.reputation = float(reputation)
        self.upgrades = dict(upgrades)
        self.stock = list(stock) if isinstance(stock, list) else []
        self.rng = streams
        self.time_left_ticks = int(self.t["max_ticks"])
        self.done = False
        self.reason = None

    def snapshot(self):
        if isinstance(self.stock, list):
            stock_snap = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]}
                          for it in sorted(self.stock, key=lambda x: x["id"])]
        else:
            stock_snap = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "stock": stock_snap,
            "upgrades": dict(self.upgrades),
            "hand": None,
            "stoves": [],
            "tables": [],
            "customers": [],
            "player": {"pos": [0.0, 0.0]},
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        buy = getattr(inp, "buy", None)
        if buy:
            events.extend(self._buy(buy))
        if inp.pressed("shop_done") or self.time_left_ticks <= 0:
            self.done = True
            self.reason = "done" if inp.pressed("shop_done") else "time"
            events.append(("shop_end", {"reason": self.reason}))
        return events

    def _buy(self, name):
        ups = self.t["upgrades"].get(name)
        if ups is None:
            return [("buy_failed", {"action": name, "reason": "unknown"})]
        cur = int(self.upgrades.get(name, 0))
        nxt = cur + 1
        row = next((r for r in ups if r["level"] == nxt), None)
        if row is None:
            return [("buy_failed", {"action": name, "reason": "max_level"})]
        price = int(row["price"])
        if self.money < price:
            return [("buy_failed", {"action": name, "reason": "funds"})]
        self.money -= price
        self.upgrades[name] = nxt
        return [("bought", {"upgrade": name, "level": nxt, "price": price, "money": self.money})]


class DaySim:
    mode = "day"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.days_target = max(1, min(5, int(days)))
        self.days_completed = 0
        day_block = scenario.get("day", {}) if isinstance(scenario, dict) else {}
        self.money = int(day_block.get("money", 0))
        self.earned = int(day_block.get("earned", 0))
        self.reputation = float(day_block.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_block.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)  # cấp đang áp (đầu game = đã mua từ trước)
        self.day_plan = list(day_block.get("day_plan") or tuning["day_plan"])
        self.gather_template = dict(scenario.get("gather", {})) if isinstance(scenario, dict) else {}
        self.quan_template = dict(scenario.get("quan", {})) if isinstance(scenario, dict) else {}
        self.day = 1
        self.phase_tick = 0
        self.done = False
        self.reason = None
        self.time_left_ticks = 0
        self.paused = False
        self._child = None
        self._pending_events = []
        self._start_day()

    def _plan_for(self, day):
        for p in self.day_plan:
            if int(p["day"]) == int(day):
                return p
        # lặp D1–D5
        return self.day_plan[(day - 1) % 5]

    def _start_day(self):
        self.phase = "gather"
        self.phase_tick = 0
        plan = self._plan_for(self.day)
        self.current_plan = {
            "dishes": dict(plan["dishes"]),
            "ingredients": dict(plan.get("ingredients") or {}),
        }
        gsc = dict(self.gather_template)
        # Ngày > 1: không giữ hold mẫu trừ khi fixture nói rõ chỉ Ngày 1
        if self.day > 1 and "hold" in gsc:
            # P3 sẽ cấp id mới; P2 hold là kind list — clear mang sang trừ khi scenario chỉ 1 ngày
            pass
        self._child = GatherSim(
            self.tuning, gsc, self.rng, self.ids,
            day=self.day, active_upgrades=self.active_upgrades,
        )
        self.time_left_ticks = self._child.time_left_ticks
        self._pending_events = [
            ("day_start", {}),
            ("day_plan", dict(self.current_plan)),
            ("phase_start", {}),
        ]

    def _start_quan(self, inventory):
        self.phase = "quan"
        self.phase_tick = 0
        qsc = dict(self.quan_template)
        self._child = QuanSim(
            self.tuning, qsc, self.rng, self.ids,
            inventory=inventory,
            money=self.money, earned=self.earned, reputation=self.reputation,
            menu_filter=list(self.current_plan["dishes"].keys()),
        )
        self.time_left_ticks = self._child.time_left_ticks
        self._pending_events.append(("phase_start", {}))

    def _start_shop(self):
        self.phase = "shop"
        self.phase_tick = 0
        child_stock = getattr(self._child, "stock", [])
        stock = list(child_stock) if isinstance(child_stock, list) else []
        self.money = self._child.money
        self.earned = self._child.earned
        self.reputation = self._child.reputation
        self._child = ShopSim(
            self.tuning, self.money, self.earned, self.reputation,
            self.upgrades, stock, self.rng,
        )
        self.time_left_ticks = self._child.time_left_ticks
        self._pending_events.append(("phase_start", {}))

    @property
    def hold(self):
        return getattr(self._child, "hold", [])

    def snapshot(self):
        snap = self._child.snapshot()
        snap.update({
            "day": self.day,
            "day_plan": dict(self.current_plan),
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        })
        return snap

    def step(self, inp):
        events = []
        # flush pending phase events first (same tick as transition)
        if self._pending_events:
            events.extend(self._pending_events)
            self._pending_events = []

        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                events.append(("paused", {}))
                return events
            self.paused = False
            events.append(("resumed", {}))
            # tiếp tục gameplay trong cùng bước

        if self.paused:
            return events

        # shop buy from frame
        if self.phase == "shop" and getattr(inp, "buy", None):
            pass  # ShopSim đọc inp.buy

        child_events = self._child.step(inp)
        self.phase_tick += 1
        self.time_left_ticks = self._child.time_left_ticks
        # sync economy from quan/shop only — GatherSim giữ money=0 cho HUD đơn buổi
        if self.phase in ("quan", "shop"):
            self.money = self._child.money
            self.earned = self._child.earned
            self.reputation = self._child.reputation
        if self.phase == "shop":
            self.upgrades = dict(self._child.upgrades)

        for name, data in child_events:
            events.append((name, data))
            if name == "gather_end":
                inv = data.get("inventory", {}).get("items", {})
                self._start_quan(inv)
                # phase_start cùng tick
                events.extend(self._pending_events)
                self._pending_events = []
            elif name == "quan_end":
                self._start_shop()
                events.extend(self._pending_events)
                self._pending_events = []
            elif name == "shop_end":
                self.days_completed += 1
                # áp cấp đã mua sang active từ Ngày kế
                self.active_upgrades = dict(self.upgrades)
                if self.days_completed >= self.days_target:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self._start_day()
                    events.extend(self._pending_events)
                    self._pending_events = []
        return events
