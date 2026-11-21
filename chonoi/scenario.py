"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json
import math

from .errors import BadInput
from .inventory import KINDS, validate_item_list, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters",
               "random_current", "current_direction"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
NODE_KEYS = {"id", "kind", "pos", "regrow_ticks"}
FISH_KEYS = {"id", "kind", "pos", "heading_deg", "age_ticks"}
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
TABLE_KEYS = {"id", "pos"}
CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                 "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
DISH_KEYS = {"order_id", "dish_id", "base_price"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {} if mode != "day" else {"gather": {}, "quan": {}, "day": {}}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")

    if mode == "day":
        if not set(data) <= {"gather", "quan", "day"}:
            raise BadInput("scenario day chỉ được có khối gather/quan/day")
        gather = data.get("gather", {})
        quan = data.get("quan", {})
        day = data.get("day", {})
        if not isinstance(gather, dict) or not isinstance(quan, dict) or not isinstance(day, dict):
            raise BadInput("khối gather/quan/day phải là object")
        if set(gather) - GATHER_KEYS:
            raise BadInput(f"trường lạ trong gather: {sorted(set(gather) - GATHER_KEYS)}")
        if set(quan) - QUAN_KEYS:
            raise BadInput(f"trường lạ trong quan: {sorted(set(quan) - QUAN_KEYS)}")
        if set(day) - DAY_KEYS:
            raise BadInput(f"trường lạ trong day: {sorted(set(day) - DAY_KEYS)}")
        if "stock" in quan or "reputation" in quan:
            raise BadInput("day cấm quan.stock và quan.reputation")
        _validate_gather(gather, tuning) if gather else None
        # quan block may omit stock; still validate other fields
        q2 = dict(quan)
        _validate_quan(q2, tuning) if q2 else None
        money, earned = day.get("money", 0), day.get("earned", 0)
        if "money" in day or "earned" in day:
            if "money" not in day or "earned" not in day:
                raise BadInput("day: khai money và earned cùng lúc")
            if not (isinstance(money, int) and isinstance(earned, int) and 0 <= money <= earned):
                raise BadInput("day: cần 0 <= money <= earned")
        return {"gather": gather, "quan": quan, "day": day}

    if not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "random_current" in b and not isinstance(b["random_current"], bool):
        raise BadInput("random_current phải là boolean")
    if "current_direction" in b and (isinstance(b["current_direction"], bool) or b["current_direction"] not in (-1, 1)):
        raise BadInput("current_direction phải là -1 hoặc 1")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list):
            raise BadInput("hold phải là mảng")
        if h and isinstance(h[0], dict):
            validate_item_list(h)
        elif any(k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        extra_n = set(n) - NODE_KEYS
        if extra_n:
            raise BadInput(f"nodes.{n['id']}: trường lạ {sorted(extra_n)}")
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        extra_f = set(f) - FISH_KEYS
        if extra_f:
            raise BadInput(f"fish.{f['id']}: trường lạ {sorted(extra_f)}")
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    if "monsters" in b:
        _check_ids("monsters", b["monsters"])
        species = set(g["monsters"]["species"])
        for m in b["monsters"]:
            extra_m = set(m) - MONSTER_KEYS
            if extra_m:
                raise BadInput(f"monsters.{m['id']}: trường lạ {sorted(extra_m)}")
            if m.get("kind") not in species:
                raise BadInput(f"monsters.{m['id']}: kind không hợp lệ")
            _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
            if "waypoints" in m:
                wps = m["waypoints"]
                if not (isinstance(wps, list) and len(wps) == 2):
                    raise BadInput(f"monsters.{m['id']}: cần đúng 2 waypoints")
                for i, wp in enumerate(wps):
                    _pos(f"monsters.{m['id']}.waypoints[{i}]", wp, bounds)


def _validate_dish_payload(name, d, menu):
    if not isinstance(d, dict) or set(d) != DISH_KEYS:
        raise BadInput(f"{name}: payload món phải có đúng khóa {sorted(DISH_KEYS)}")
    if not isinstance(d["order_id"], str) or not d["order_id"]:
        raise BadInput(f"{name}: order_id không hợp lệ")
    if d["dish_id"] not in menu:
        raise BadInput(f"{name}: dish_id lạ {d['dish_id']!r}")
    bp = d["base_price"]
    if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
        raise BadInput(f"{name}: base_price phải là số nguyên dương")


def _validate_quan(b, tuning):
    q = tuning["quan"]
    menu = tuning["menu"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("quan.reputation ngoài miền [reputation_min, reputation_max]")
    if "stock" in b:
        st = b["stock"]
        if isinstance(st, dict):
            # fixture đếm: quan sẽ đổi sang cá thể
            for k, v in st.items():
                if k not in KINDS:
                    raise BadInput(f"nguyên liệu lạ: {k}")
                if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                    raise BadInput(f"số lượng không hợp lệ cho {k}")
        else:
            validate_item_list(st)
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = q["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_stoves = {s["id"] for s in q["stoves"]}
    assigned_dishes = []
    for s in b.get("stoves", []):
        extra_s = set(s) - STOVE_KEYS
        if extra_s:
            raise BadInput(f"stoves.{s['id']}: trường lạ {sorted(extra_s)}")
        if s["id"] not in known_stoves:
            raise BadInput(f"stoves.{s['id']}: id bếp không tồn tại")
        if "pos" in s:
            _pos(f"stoves.{s['id']}.pos", s["pos"], qb, axes=("x", "z"))
        st = s.get("state", "idle")
        if st not in ("idle", "cooking", "ready"):
            raise BadInput(f"stoves.{s['id']}.state không hợp lệ: {st!r}")
        ct = s.get("cook_ticks_left", 0)
        rt = s.get("ready_ticks", 0)
        _nonneg_int(f"stoves.{s['id']}.cook_ticks_left", ct)
        _nonneg_int(f"stoves.{s['id']}.ready_ticks", rt)
        dish = s.get("dish")
        if st == "idle":
            if dish is not None or ct != 0 or rt != 0:
                raise BadInput(f"stoves.{s['id']}: bếp idle không được có món/timer")
        elif st == "cooking":
            if ct <= 0:
                raise BadInput(f"stoves.{s['id']}: bếp cooking phải có cook_ticks_left > 0")
            _validate_dish_payload(f"stoves.{s['id']}.dish", dish, menu)
            assigned_dishes.append(dish)
        else:
            if ct != 0:
                raise BadInput(f"stoves.{s['id']}: bếp ready phải có cook_ticks_left == 0")
            _validate_dish_payload(f"stoves.{s['id']}.dish", dish, menu)
            assigned_dishes.append(dish)

    known_tables = {t["id"] for t in q["tables"]}
    for tb in b.get("tables", []):
        extra_tb = set(tb) - TABLE_KEYS
        if extra_tb:
            raise BadInput(f"tables.{tb['id']}: trường lạ {sorted(extra_tb)}")
        if tb["id"] not in known_tables:
            raise BadInput(f"tables.{tb['id']}: id bàn không tồn tại")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, axes=("x", "z"))

    hand = b.get("hand")
    if hand is not None:
        _validate_dish_payload("quan.hand", hand, menu)
        assigned_dishes.append(hand)

    customers = b.get("customers", [])
    table_ids = [c.get("table_id") for c in customers]
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    patience_max = int(round(q["patience_s"] * 60))
    by_id = {}
    total_reserved = {}
    for c in customers:
        cid = c["id"]
        extra_c = set(c) - CUSTOMER_KEYS
        if extra_c:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(extra_c)}")
        by_id[cid] = c
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        dish_id = c.get("dish_id")
        if dish_id not in menu:
            raise BadInput(f"customers.{cid}: dish_id không hợp lệ: {dish_id!r}")
        if "order_tick" in c:
            _nonneg_int(f"customers.{cid}.order_tick", c["order_tick"])
        cstate = c.get("state", "waiting")
        if cstate not in ("waiting", "eating"):
            raise BadInput(f"customers.{cid}.state không hợp lệ: {cstate!r}")
        if "patience_ticks_left" in c:
            _nonneg_int(f"customers.{cid}.patience_ticks_left", c["patience_ticks_left"])
            if c["patience_ticks_left"] > patience_max:
                raise BadInput(f"customers.{cid}.patience_ticks_left vượt tối đa")
        if "eat_ticks_left" in c:
            _nonneg_int(f"customers.{cid}.eat_ticks_left", c["eat_ticks_left"])
        ost = c.get("order_status", "reserved")
        if ost not in ("reserved", "assigned", "unfulfillable", "served"):
            raise BadInput(f"customers.{cid}.order_status không hợp lệ: {ost!r}")
        if "reserved" in c:
            res = validate_items(c["reserved"])
            if ost == "reserved" and res != menu[dish_id]["recipe"]:
                raise BadInput(f"customers.{cid}: reserved khác công thức món {dish_id}")
            if ost != "reserved" and res:
                raise BadInput(f"customers.{cid}: đơn {ost} phải có reserved rỗng")
        else:
            res = dict(menu[dish_id]["recipe"]) if ost == "reserved" else {}
        for k, v in res.items():
            total_reserved[k] = total_reserved.get(k, 0) + v

        if cstate == "eating":
            if ost != "served":
                raise BadInput(f"customers.{cid}: khách eating phải có order_status='served'")
            if c.get("eat_ticks_left", 0) <= 0:
                raise BadInput(f"customers.{cid}: khách eating phải có eat_ticks_left > 0")
            bp = c.get("base_price")
            tip = c.get("tip")
            if isinstance(bp, bool) or not isinstance(bp, int) or bp <= 0:
                raise BadInput(f"customers.{cid}: khách eating cần base_price nguyên dương")
            _nonneg_int(f"customers.{cid}.tip", tip)
        else:
            if ost == "served":
                raise BadInput(f"customers.{cid}: khách waiting không thể có order_status='served'")
            if c.get("eat_ticks_left", 0) != 0:
                raise BadInput(f"customers.{cid}: khách waiting phải có eat_ticks_left == 0")

    if "stock" in b:
        stock = b["stock"]
        for k, qty in total_reserved.items():
            if qty > stock.get(k, 0):
                raise BadInput(f"tổng giữ chỗ {k}={qty} vượt quá kho {stock.get(k, 0)}")

    counts = {}
    for d in assigned_dishes:
        oid = d["order_id"]
        c = by_id.get(oid)
        if c is None or c.get("order_status", "reserved") != "assigned":
            raise BadInput(f"món trên bếp/tay trỏ tới đơn không ở trạng thái assigned: {oid}")
        if d["dish_id"] != c["dish_id"]:
            raise BadInput(f"món {d['dish_id']} không khớp đơn {oid} ({c['dish_id']})")
        counts[oid] = counts.get(oid, 0) + 1
    for cid, c in by_id.items():
        if c.get("order_status", "reserved") == "assigned" and counts.get(cid, 0) != 1:
            raise BadInput(f"đơn assigned {cid} phải có đúng 1 món ở bếp hoặc tay (đang có {counts.get(cid, 0)})")
