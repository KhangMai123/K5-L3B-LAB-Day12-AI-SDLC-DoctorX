"""Đọc game.contract.json và kiểm dải hợp lệ (Test Contract v1.1)."""

import json
import math
import os

from .errors import BadInput

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")

REQUIRED_RECIPES = {
    "ca_loc_nuong_trui": {"ca_loc": 1},
    "goi_bong_sung": {"bong_sung": 2},
    "lau_ca_linh_dien_dien": {"ca_linh": 3, "bong_dien_dien": 1},
    "canh_chua_ca_loc": {"ca_loc": 1, "bong_dien_dien": 1},
    "ca_keo_nuong": {"ca_keo": 2},
    "lau_mam": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1},
}

NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if not isinstance(c, dict):
        raise BadInput("game.contract.json phải là object")
    if c.get("contract_version") != "1.3":
        raise BadInput(f"contract_version phải là '1.3', đang là {c.get('contract_version')!r}")
    for key in ("team", "headless_cmd", "run_cmd", "build_cmd", "bench_cmd", "soak_cmd"):
        if not isinstance(c.get(key), str) or not c[key].strip():
            raise BadInput(f"thiếu hoặc sai {key} trong game.contract.json")
    ts = c.get("team_size")
    if isinstance(ts, bool) or not isinstance(ts, int) or ts <= 0:
        raise BadInput(f"team_size phải là số nguyên dương, đang là {ts!r}")
    validate_tuning(c.get("tuning"), extensions=c.get("extensions") or [])
    return c


def _validate_gather(g):
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")

    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or set(fy) != set(FISH_KINDS):
        raise BadInput("tuning.gather.fish_yield phải có đúng ca_linh, ca_loc, ca_keo")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])

    _int_between("gather.fish_initial", g.get("fish_initial"), 1, 12)
    _between("gather.fish_speed", g.get("fish_speed"), 0.1, 10)
    _int_between("gather.fish_turn_ticks", g.get("fish_turn_ticks"), 1, 10_000)
    _int_between("gather.fish_max", g.get("fish_max"), 1, 30)
    _int_between("gather.fish_spawn_ticks", g.get("fish_spawn_ticks"), 1, 10_000)
    _between("gather.fish_spawn_clearance", g.get("fish_spawn_clearance"), 0.1, 10)
    fx = g.get("fish_x")
    if not (isinstance(fx, list) and len(fx) == 2 and all(_num(c) for c in fx) and fx[0] < fx[1]):
        raise BadInput("tuning.gather.fish_x phải là [lo, hi]")
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights"):
        m = g.get(key)
        if not isinstance(m, dict) or set(m) != set(FISH_KINDS):
            raise BadInput(f"tuning.gather.{key} phải có đúng 3 loài")
    for k in FISH_KINDS:
        d = g["fish_depths"][k]
        if not (isinstance(d, list) and len(d) == 2 and all(_num(c) for c in d)):
            raise BadInput(f"tuning.gather.fish_depths.{k} phải là [lo, hi]")
        sd = g["fish_spawn_depths"][k]
        if not (isinstance(sd, list) and len(sd) >= 1 and all(_num(c) for c in sd)):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{k} phải là mảng số")
        _between(f"gather.fish_weights.{k}", g["fish_weights"][k], 0, 1)
    sx = g.get("fish_spawn_x")
    if not isinstance(sx, list) or not sx or not all(_num(c) for c in sx):
        raise BadInput("tuning.gather.fish_spawn_x phải là mảng số không rỗng")

    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind không hợp lệ")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    for need in ("bong_dien_dien", "bong_sung", "keo_neo"):
        if need not in kinds:
            raise BadInput(f"tuning.gather.nodes phải có ít nhất một nút {need}")

    monsters = g.get("monsters")
    if not isinstance(monsters, dict):
        raise BadInput("tuning.gather.monsters phải là object")
    _int_between("gather.monsters.invuln_ticks", monsters.get("invuln_ticks"), 1, 10_000)
    _between("gather.monsters.loss_ratio", monsters.get("loss_ratio"), 0, 1)
    species = monsters.get("species")
    if not isinstance(species, dict) or "ca_sau" not in species:
        raise BadInput("tuning.gather.monsters.species phải có ca_sau")
    for sk, sp in species.items():
        if not isinstance(sp, dict):
            raise BadInput(f"tuning.gather.monsters.species.{sk} phải là object")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            if not _num(sp.get(key)) or sp[key] <= 0:
                raise BadInput(f"tuning.gather.monsters.species.{sk}.{key} phải > 0")
        depths = sp.get("depths")
        if not (isinstance(depths, list) and len(depths) == 2 and all(_num(c) for c in depths)):
            raise BadInput(f"tuning.gather.monsters.species.{sk}.depths phải là [lo, hi]")
        _int_between(f"gather.monsters.species.{sk}.recoil_ticks", sp.get("recoil_ticks"), 1, 10_000)
    spawns = monsters.get("spawns")
    if not isinstance(spawns, list) or not spawns:
        raise BadInput("tuning.gather.monsters.spawns phải là mảng không rỗng")
    seen = set()
    for s in spawns:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or s["id"] in seen:
            raise BadInput("monsters.spawns: mỗi spawn cần id duy nhất")
        seen.add(s["id"])
        if s.get("kind") not in species:
            raise BadInput(f"monsters.spawns.{s['id']}: kind không có trong species")
        _pos_in(f"monsters.spawns.{s['id']}.pos", s.get("pos"), b, ("x", "d"))
        wps = s.get("waypoints")
        if not (isinstance(wps, list) and len(wps) == 2):
            raise BadInput(f"monsters.spawns.{s['id']}: cần đúng 2 waypoints")
        for i, wp in enumerate(wps):
            _pos_in(f"monsters.spawns.{s['id']}.waypoints[{i}]", wp, b, ("x", "d"))
        _int_between(f"monsters.spawns.{s['id']}.from_day", s.get("from_day"), 1, 5)


def _validate_quan(q, extensions):
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    qb = q["bounds"]
    _pos_in("quan.start_pos", q.get("start_pos"), qb, ("x", "z"))
    stoves = q.get("stoves")
    if not isinstance(stoves, list) or {s.get("id") for s in stoves} != {"B1", "B2"}:
        raise BadInput("tuning.quan.stoves phải có đúng B1 và B2")
    for s in stoves:
        _pos_in(f"quan.stoves.{s['id']}.pos", s.get("pos"), qb, ("x", "z"))
    tables = q.get("tables")
    if not isinstance(tables, list) or {t.get("id") for t in tables} != {"T1", "T2", "T3", "T4"}:
        raise BadInput("tuning.quan.tables phải có đúng T1–T4")
    for tb in tables:
        _pos_in(f"quan.tables.{tb['id']}.pos", tb.get("pos"), qb, ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    _int_between("quan.carry_limit", q.get("carry_limit"), 1, 99)
    rmin, rmax, rinit = q.get("reputation_min"), q.get("reputation_max"), q.get("reputation_initial")
    if not (_num(rmin) and _num(rmax) and _num(rinit) and 0 <= rmin <= rinit <= rmax):
        raise BadInput("reputation_min <= reputation_initial <= reputation_max và >= 0")
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    burn = q.get("burn_s")
    if "burn" in extensions:
        if not (_num(burn) and burn > 0):
            raise BadInput("quan.burn_s phải > 0 khi bật mở rộng burn")
    elif burn is not None:
        raise BadInput("burn_s phải là null khi chưa bật mở rộng burn")


def _validate_menu(menu):
    if set(menu.keys()) != set(REQUIRED_RECIPES.keys()):
        raise BadInput(f"tuning.menu phải có đúng 6 món {sorted(REQUIRED_RECIPES)}")
    for dish_id, d in menu.items():
        if not isinstance(d, dict) or d.get("recipe") != REQUIRED_RECIPES[dish_id]:
            raise BadInput(f"menu.{dish_id}.recipe phải là {REQUIRED_RECIPES[dish_id]}")
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")


def _validate_day_plan(plan, menu):
    if not isinstance(plan, list) or len(plan) != 5:
        raise BadInput("tuning.day_plan phải có đúng 5 Ngày")
    for i, entry in enumerate(plan, start=1):
        if not isinstance(entry, dict) or entry.get("day") != i:
            raise BadInput(f"day_plan[{i-1}].day phải là {i}")
        dishes = entry.get("dishes")
        if not isinstance(dishes, dict) or not dishes:
            raise BadInput(f"day_plan[{i}].dishes phải là object không rỗng")
        expected = {}
        for dish_id, qty in dishes.items():
            if dish_id not in menu:
                raise BadInput(f"day_plan[{i}]: món {dish_id} không có trong menu")
            _int_between(f"day_plan[{i}].dishes.{dish_id}", qty, 1, 99)
            for kind, n in menu[dish_id]["recipe"].items():
                expected[kind] = expected.get(kind, 0) + n * qty
        ingredients = entry.get("ingredients")
        if ingredients is not None and ingredients != expected:
            raise BadInput(f"day_plan[{i}].ingredients không khớp công thức × suất")


def _validate_shop(shop, extensions=()):
    if not isinstance(shop, dict):
        raise BadInput("tuning.shop phải là object")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 10_000)
    upgrades = shop.get("upgrades")
    if not isinstance(upgrades, dict) or "oxygen" not in upgrades or "hp" not in upgrades:
        raise BadInput("tuning.shop.upgrades phải có oxygen và hp")
    specs = [("oxygen", ("level", "price", "oxygen_max_s")), ("hp", ("level", "price", "hp_max"))]
    if "net" in extensions:
        if "net" not in upgrades:
            raise BadInput("extensions có net nhưng thiếu tuning.shop.upgrades.net")
        specs.append(("net", ("level", "price", "catch_radius", "max_schools")))
    for name, keys in specs:
        arr = upgrades[name]
        if not isinstance(arr, list) or len(arr) != 2:
            raise BadInput(f"shop.upgrades.{name} phải có đúng 2 cấp")
        for i, row in enumerate(arr, start=1):
            if not isinstance(row, dict) or row.get("level") != i:
                raise BadInput(f"shop.upgrades.{name}[{i-1}].level phải là {i}")
            for k in keys:
                if k == "level":
                    continue
                v = row.get(k)
                if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                    raise BadInput(f"shop.upgrades.{name}[{i}].{k} phải > 0")


def validate_tuning(t, extensions=None):
    extensions = list(extensions or [])
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    if t.get("tick_hz") != 60:
        raise BadInput(f"tuning.tick_hz phải là 60, đang là {t.get('tick_hz')!r}")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    if "current" in extensions:
        cur = g.get("current")
        if not isinstance(cur, dict):
            raise BadInput("extensions có current nhưng thiếu tuning.gather.current")
        for k in ("interval_ticks", "duration_ticks", "warning_ticks"):
            _int_between(f"gather.current.{k}", cur.get(k), 1, 100_000)
        _between("gather.current.min_depth", cur.get("min_depth"), 0, 30)
        _between("gather.current.speed", cur.get("speed"), 0, 20)
    _validate_quan(q, extensions)
    _validate_menu(menu)
    _validate_day_plan(t.get("day_plan"), menu)
    _validate_shop(t.get("shop"), extensions)
    fr = t.get("freshness")
    if not isinstance(fr, dict):
        raise BadInput("tuning.freshness phải là object")
    _between("freshness.initial", fr.get("initial"), 0, 100)
    _between("freshness.gather_decay_per_s", fr.get("gather_decay_per_s"), 0, 100)
    _between("freshness.quan_decay_per_s", fr.get("quan_decay_per_s"), 0, 100)
    _between("freshness.spoiled_below", fr.get("spoiled_below"), 0, 100)
    sc = t.get("score")
    if not isinstance(sc, dict) or not _num(sc.get("reputation_multiplier")) or sc["reputation_multiplier"] < 0:
        raise BadInput("tuning.score.reputation_multiplier phải là số >= 0")
