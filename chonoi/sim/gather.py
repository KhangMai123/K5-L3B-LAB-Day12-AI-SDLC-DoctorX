"""Buổi sáng — Lặn & Hái (`gather`), Phase 2 (cá bơi/sinh, Cá Sấu)."""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


def _unit(dx, dy):
    n = math.hypot(dx, dy)
    if n <= 1e-12:
        return (1.0, 0.0)
    return (dx / n, dy / n)


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active_upgrades=None):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.day = int(day)
        self.active_upgrades = dict(active_upgrades or {})
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        oxy_s = t["oxygen_max_s"]
        hp_max = t["hp_max"]
        if self.active_upgrades.get("oxygen"):
            lvl = int(self.active_upgrades["oxygen"])
            for row in tuning["shop"]["upgrades"]["oxygen"]:
                if row["level"] == lvl:
                    oxy_s = row["oxygen_max_s"]
        if self.active_upgrades.get("hp"):
            lvl = int(self.active_upgrades["hp"])
            for row in tuning["shop"]["upgrades"]["hp"]:
                if row["level"] == lvl:
                    hp_max = row["hp_max"]
        self.oxygen_max = int(round(oxy_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp_max = int(hp_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.fresh_cfg = tuning["freshness"]
        # đơn vị nội bộ: 240 mỗi điểm fresh; gather −2/tick (= 0.5/s)
        self._fresh_units_per_point = 240
        self._gather_decay_units = 2
        self.hold = self._parse_hold(scenario.get("hold", []), ids)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0
        self.random_fish = scenario.get("random_fish", True)

        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        if "fish" in scenario:
            src_fish = scenario["fish"]
            self.fish = [self._fish_from(f) for f in src_fish]
        elif self.random_fish:
            self.fish = []
            self._spawn_initial_fish()
        else:
            self.fish = []

        if "monsters" in scenario:
            src_m = scenario["monsters"]
        else:
            src_m = [s for s in t["monsters"]["spawns"] if int(s.get("from_day", 1)) <= self.day]
        self.monsters = [self._monster_from(m) for m in src_m]

        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _fish_from(self, f):
        return {
            "id": f["id"], "kind": f["kind"],
            "pos": [float(c) for c in f["pos"]],
            "heading_deg": float(f.get("heading_deg", 0)),
            "age_ticks": int(f.get("age_ticks", 0)),
        }

    def _monster_from(self, m):
        wps = m.get("waypoints") or [m["pos"], m["pos"]]
        return {
            "id": m["id"], "kind": m["kind"],
            "pos": [float(c) for c in m["pos"]],
            "waypoints": [[float(c) for c in w] for w in wps],
            "target_idx": int(m.get("target_idx", 1)),
            "state": m.get("state", "patrol"),
            "state_ticks_left": int(m.get("state_ticks_left", 0)),
            "recoil_dir": m.get("recoil_dir"),
        }

    def _parse_hold(self, raw, ids):
        initial = float(self.fresh_cfg["initial"])
        out = []
        for h in raw:
            if isinstance(h, str):
                out.append({
                    "id": ids.new("I"), "kind": h, "fresh": initial,
                    "_units": int(round(initial * self._fresh_units_per_point)),
                })
            else:
                fresh = float(h.get("fresh", initial))
                if "id" in h:
                    ids.reserve(h["id"])
                    iid = h["id"]
                else:
                    iid = ids.new("I")
                out.append({
                    "id": iid, "kind": h["kind"], "fresh": fresh,
                    "_units": int(round(fresh * self._fresh_units_per_point)),
                })
        return out

    def inventory_items(self):
        return hold_to_items([{"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]} for h in self.hold])

    def free_hold_slots(self) -> int:
        return max(0, int(self.t["hold_capacity"]) - len(self.hold))

    def can_hold(self, n: int) -> bool:
        return n >= 0 and n <= self.free_hold_slots()

    def push_hold(self, kinds) -> None:
        initial = float(self.fresh_cfg["initial"])
        for k in kinds:
            if isinstance(k, dict):
                self.hold.append(k)
            else:
                self.hold.append({
                    "id": self.ids.new("I"), "kind": k, "fresh": initial,
                    "_units": int(round(initial * self._fresh_units_per_point)),
                })

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [{"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]} for h in self.hold],
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{
                "id": m["id"], "kind": m["kind"], "pos": m["pos"],
                "waypoints": m["waypoints"], "target_idx": m["target_idx"],
                "state": m["state"], "state_ticks_left": m["state_ticks_left"],
                "recoil_dir": m["recoil_dir"],
            } for m in sort_by_id(self.monsters)],
        }

    def _decay_hold(self, events):
        threshold = float(self.fresh_cfg["spoiled_below"])
        spoiled = []
        for h in self.hold:
            before = h["fresh"]
            h["_units"] = max(0, h["_units"] - self._gather_decay_units)
            h["fresh"] = h["_units"] / self._fresh_units_per_point
            if before >= threshold and h["fresh"] < threshold:
                spoiled.append(h)
        for h in sorted(spoiled, key=lambda x: x["id"]):
            events.append(("spoiled", {"item_id": h["id"], "kind": h["kind"], "location": "hold"}))

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        self._decay_hold(events)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if self._apply_oxygen(events):
            self.phase_tick += 1
            return events

        if self._update_monsters_and_hit(events):
            self.phase_tick += 1
            return events

        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                self.phase_tick += 1
                return events
            self._gather(events)

        catch_pos_fish = [{**f, "pos": list(f["pos"])} for f in self.fish]
        if inp.pressed("catch"):
            self._catch(events, catch_pos_fish)

        if self.time_left_ticks <= 0:
            self._finish("time", events)
            self.phase_tick += 1
            return events

        if self.random_fish:
            self._swim_fish()
            events.extend(self._maybe_spawn_fish())
        self.phase_tick += 1
        return events

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _nearest_in_radius(self, entities, radius, pos=None):
        origin = pos or self.pos
        nearby = [e for e in sort_by_id(entities) if math.dist(origin, e["pos"]) <= radius]
        return min(nearby, key=lambda e: math.dist(origin, e["pos"]), default=None)

    def _gather(self, events):
        if not self._at_surface():
            return
        node = self._nearest_in_radius(
            [n for n in self.nodes if n["regrow_ticks"] == 0], self.t["interact_radius"])
        if node is None:
            return
        count = self.t["node_yield"]
        if not self.can_hold(count):
            events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                         "required": count, "free": self.free_hold_slots()}))
            return
        self.push_hold([node["kind"]] * count)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": count}))

    def _net_row(self):
        """Mở rộng `net`: dòng cấp đang áp dụng; None = cấp 0, dùng luật gần nhất của lõi."""
        lvl = int(self.active_upgrades.get("net", 0) or 0)
        rows = self.tuning.get("shop", {}).get("upgrades", {}).get("net", [])
        return next((r for r in rows if r["level"] == lvl), None) if lvl > 0 else None

    def _catch_net(self, events, fish_snapshot, row):
        """Từ cấp 1: duyệt đàn trong catch_radius theo id, tối đa max_schools đàn bắt thành công.
        Đàn thiếu chỗ phát hold_full, được giữ lại và xét đàn kế; có đàn bắt được mới đặt hồi."""
        caught = 0
        for fish in sort_by_id(fish_snapshot):
            if caught >= int(row["max_schools"]):
                break
            if math.dist(self.pos, fish["pos"]) > row["catch_radius"]:
                continue
            live = next((f for f in self.fish if f["id"] == fish["id"]), None)
            if live is None:
                continue
            count = self.t["fish_yield"][live["kind"]]
            if not self.can_hold(count):
                events.append(("hold_full", {"action": "catch", "fish_id": live["id"],
                                             "required": count, "free": self.free_hold_slots()}))
                continue
            self.push_hold([live["kind"]] * count)
            self.fish.remove(live)
            caught += 1
            events.append(("fish_caught", {"fish_id": live["id"], "kind": live["kind"], "yield": count}))
        if caught:
            self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))

    def _catch(self, events, fish_snapshot):
        if self._at_surface() or self.catch_cd_ticks > 0:
            return
        row = self._net_row()
        if row is not None:
            self._catch_net(events, fish_snapshot, row)
            return
        fish = self._nearest_in_radius(fish_snapshot, self.t["catch_radius"])
        if fish is None:
            return
        live = next((f for f in self.fish if f["id"] == fish["id"]), None)
        if live is None:
            return
        count = self.t["fish_yield"][live["kind"]]
        if not self.can_hold(count):
            events.append(("hold_full", {"action": "catch", "fish_id": live["id"],
                                         "required": count, "free": self.free_hold_slots()}))
            return
        self.push_hold([live["kind"]] * count)
        self.fish.remove(live)
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        events.append(("fish_caught", {"fish_id": live["id"], "kind": live["kind"], "yield": count}))

    def _apply_oxygen(self, events) -> bool:
        if self._at_surface():
            refill = int(self.t["oxygen_refill_per_tick"])
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
            return False
        before = self.oxygen_ticks
        self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
        if before > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks == 0:
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= int(self.t["choke_interval_ticks"]):
                self.zero_oxy_ticks = 0
                self.hp -= 1
                events.append(("choke", {"hp": self.hp}))
                if self.hp <= 0:
                    lost = [{"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]}
                            for h in reversed(self.hold)]
                    self.hold.clear()
                    events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                    self._finish("fainted", events)
                    return True
        return False

    def _species(self, kind):
        return self.t["monsters"]["species"][kind]

    def _clamp_monster(self, m, pos):
        sp = self._species(m["kind"])
        b = self.t["bounds"]
        x = min(b["x"][1], max(b["x"][0], pos[0]))
        dlo, dhi = sp["depths"]
        d = min(min(b["d"][1], dhi), max(max(b["d"][0], dlo), pos[1]))
        return [x, d]

    def _update_monsters_and_hit(self, events) -> bool:
        for m in sort_by_id(self.monsters):
            self._move_monster(m)
        if self.invuln_ticks > 0 or self.pos[1] < 10:
            return False
        hitters = [m for m in sort_by_id(self.monsters)
                   if m["state"] != "recoil"
                   and math.dist(self.pos, m["pos"]) <= self._species(m["kind"])["hit_radius"]
                   and self.pos[1] >= 10]
        if not hitters:
            return False
        m = min(hitters, key=lambda e: (math.dist(self.pos, e["pos"]), e["id"]))
        self.hp -= 1
        n_drop = int(math.floor(len(self.hold) * float(self.t["monsters"]["loss_ratio"])))
        lost = []
        for _ in range(n_drop):
            if self.hold:
                h = self.hold.pop()
                lost.append({"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]})
        self.invuln_ticks = int(self.t["monsters"]["invuln_ticks"])
        rdx, rdy = _unit(self.pos[0] - m["pos"][0], self.pos[1] - m["pos"][1])
        if math.hypot(self.pos[0] - m["pos"][0], self.pos[1] - m["pos"][1]) <= 1e-12:
            rdx, rdy = 1.0, 0.0
        m["state"] = "recoil"
        m["state_ticks_left"] = int(self._species(m["kind"])["recoil_ticks"])
        m["recoil_dir"] = [rdx, rdy]
        events.append(("monster_hit", {
            "monster_id": m["id"], "hp": self.hp, "lost": lost, "pos": list(self.pos),
        }))
        if self.hp <= 0:
            remaining = [{"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]}
                         for h in reversed(self.hold)]
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": remaining, "hp": 0}))
            self._finish("fainted", events)
            return True
        return False

    def _move_monster(self, m):
        sp = self._species(m["kind"])
        if m["state"] == "recoil":
            step = sp["recoil_dist"] / sp["recoil_ticks"]
            nx = m["pos"][0] + m["recoil_dir"][0] * step
            nd = m["pos"][1] + m["recoil_dir"][1] * step
            m["pos"] = self._clamp_monster(m, [nx, nd])
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] <= 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
                m["state_ticks_left"] = 0
            return

        player_deep = self.pos[1] >= 10
        dist = math.dist(self.pos, m["pos"])
        if m["state"] == "chase":
            if (not player_deep) or dist > sp["exit_radius"]:
                m["state"] = "patrol"
            else:
                ux, uy = _unit(self.pos[0] - m["pos"][0], self.pos[1] - m["pos"][1])
                speed = sp["chase_speed"]
                m["pos"] = self._clamp_monster(m, [
                    m["pos"][0] + ux * speed / TICK,
                    m["pos"][1] + uy * speed / TICK,
                ])
                return
        if player_deep and dist <= sp["detect_radius"]:
            m["state"] = "chase"
            ux, uy = _unit(self.pos[0] - m["pos"][0], self.pos[1] - m["pos"][1])
            speed = sp["chase_speed"]
            m["pos"] = self._clamp_monster(m, [
                m["pos"][0] + ux * speed / TICK,
                m["pos"][1] + uy * speed / TICK,
            ])
            return

        # patrol
        m["state"] = "patrol"
        target = m["waypoints"][m["target_idx"] % 2]
        dx, dy = target[0] - m["pos"][0], target[1] - m["pos"][1]
        dist_wp = math.hypot(dx, dy)
        step = sp["patrol_speed"] / TICK
        if dist_wp <= step:
            m["pos"] = self._clamp_monster(m, list(target))
            m["target_idx"] = 1 - (m["target_idx"] % 2)
        else:
            ux, uy = _unit(dx, dy)
            m["pos"] = self._clamp_monster(m, [m["pos"][0] + ux * step, m["pos"][1] + uy * step])

    def _heading_vec(self, deg):
        rad = math.radians(deg)
        return (math.cos(rad), math.sin(rad))

    def _swim_fish(self):
        speed = self.t["fish_speed"]
        xlo, xhi = self.t["fish_x"]
        turn = int(self.t["fish_turn_ticks"])
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] > 0 and f["age_ticks"] % turn == 0:
                # đổi hướng theo seed trước khi di chuyển
                rng = self.rng.get("fish_turn")
                f["heading_deg"] = rng.uniform(0, 360)
            dlo, dhi = self.t["fish_depths"][f["kind"]]
            remaining = speed / TICK
            for _ in range(4):
                if remaining <= 1e-12:
                    break
                ux, uy = self._heading_vec(f["heading_deg"])
                nx = f["pos"][0] + ux * remaining
                nd = f["pos"][1] + uy * remaining
                hit = False
                if nx < xlo:
                    over = xlo - nx
                    nx = xlo + over
                    ux = -ux
                    hit = True
                elif nx > xhi:
                    over = nx - xhi
                    nx = xhi - over
                    ux = -ux
                    hit = True
                if nd < dlo:
                    over = dlo - nd
                    nd = dlo + over
                    uy = -uy
                    hit = True
                elif nd > dhi:
                    over = nd - dhi
                    nd = dhi - over
                    uy = -uy
                    hit = True
                f["pos"] = [nx, nd]
                if hit:
                    f["heading_deg"] = math.degrees(math.atan2(uy, ux)) % 360
                    remaining = 0  # phản xạ phần còn lại đã cộng vào pos ở trên một lần
                else:
                    remaining = 0

    def _spawn_points(self, kind):
        pts = []
        for x in self.t["fish_spawn_x"]:
            for d in self.t["fish_spawn_depths"][kind]:
                pts.append((float(x), float(d)))
        return pts

    def _spawn_initial_fish(self):
        n = int(self.t["fish_initial"])
        used = set()
        for _ in range(n):
            kind, pos, heading = self._pick_spawn(used)
            if kind is None:
                break
            used.add((pos[0], pos[1]))
            fid = self.ids.new("F")
            self.fish.append({
                "id": fid, "kind": kind, "pos": list(pos),
                "heading_deg": heading, "age_ticks": 0,
            })

    def _pick_spawn(self, used_positions):
        rng = self.rng.get("fish_spawn")
        weights = self.t["fish_weights"]
        # filter kinds that still have free points
        valid_kinds = []
        for kind in sorted(weights):
            pts = [p for p in self._spawn_points(kind)
                   if p not in used_positions
                   and all(math.dist(p, f["pos"]) > self.t["fish_spawn_clearance"] for f in self.fish)]
            if pts:
                valid_kinds.append(kind)
        if not valid_kinds:
            return None, None, None
        # normalize weights among valid
        total = sum(weights[k] for k in valid_kinds)
        r = rng.random() * total
        acc = 0.0
        chosen = valid_kinds[-1]
        for k in valid_kinds:
            acc += weights[k]
            if r <= acc:
                chosen = k
                break
        pts = [p for p in self._spawn_points(chosen)
               if p not in used_positions
               and all(math.dist(p, f["pos"]) > self.t["fish_spawn_clearance"] for f in self.fish)]
        pos = pts[rng.randrange(len(pts))]
        heading = rng.uniform(0, 360)
        return chosen, pos, heading

    def _maybe_spawn_fish(self):
        events = []
        # phase_tick after increment happens at end; use upcoming value: current phase_tick is before bump
        # spawn at phase_tick = 360*k for k>=1 AFTER fish swim. We'll check after increment conceptually:
        next_pt = self.phase_tick + 1
        if next_pt == 0 or next_pt % int(self.t["fish_spawn_ticks"]) != 0:
            return events
        if len(self.fish) >= int(self.t["fish_max"]):
            return events
        used = {(f["pos"][0], f["pos"][1]) for f in self.fish}
        kind, pos, heading = self._pick_spawn(used)
        if kind is None:
            return events
        fid = self.ids.new("F")
        fish = {"id": fid, "kind": kind, "pos": list(pos), "heading_deg": heading, "age_ticks": 0}
        self.fish.append(fish)
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": list(pos)}))
        return events

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
