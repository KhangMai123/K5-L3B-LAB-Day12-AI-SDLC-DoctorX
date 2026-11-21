"""Tạo lại bằng chứng Phase 2–4 từ các lần chạy thật: python3 tools/make_proof.py [--skip-bench]

Mỗi file log ghi commit, lệnh đã chạy, mã thoát và kết quả kiểm. Chạy lại trên commit gắn tag để
bằng chứng khớp commit bàn giao. Chỉ dùng thư viện chuẩn; gọi headless bằng chính trình thông dịch đang chạy.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOF = os.path.join(ROOT, "docs", "proof")
PY = sys.executable


def commit():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


class Log:
    def __init__(self, path, title):
        self.path, self.lines, self.ok = path, [f"# {title}", f"commit: {commit()}", ""], True

    def run(self, *args, expect=0):
        cmd = [PY, "-m", *args]
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        dt = time.perf_counter() - t0
        shown = " ".join(["python3", "-m", *[os.path.relpath(a, ROOT) if os.path.isabs(a) else a for a in args]])
        self.lines.append(f"$ {shown}")
        self.lines.append(f"exit {p.returncode} ({dt:.2f} s){'' if p.returncode == expect else f'  <-- MONG {expect}'}")
        if p.stderr.strip():
            self.lines.append("stderr: " + p.stderr.strip().splitlines()[-1])
        self.ok &= p.returncode == expect
        return p, dt

    def check(self, label, cond, detail=""):
        self.ok &= bool(cond)
        self.lines.append(f"[{'ĐẠT' if cond else 'KHÔNG ĐẠT'}] {label}" + (f" — {detail}" if detail else ""))

    def note(self, s=""):
        self.lines.append(s)

    def save(self):
        self.lines += ["", f"KẾT LUẬN: {'ĐẠT' if self.ok else 'KHÔNG ĐẠT'}"]
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(self.lines) + "\n")
        print(("OK  " if self.ok else "FAIL") + "  " + os.path.relpath(self.path, ROOT))
        return self.ok


def jl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def wj(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def same_items(a, b, tol=0.01):
    """So id/kind chính xác, fresh theo dung sai quan sát ±0.01 (JSONL làm tròn 3 chữ số)."""
    return (len(a) == len(b) and all(x["id"] == y["id"] and x["kind"] == y["kind"] and abs(x["fresh"] - y["fresh"]) <= tol
                                     for x, y in zip(a, b)))


def events(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def phase2(tmp):
    ok = True
    d = os.path.join(PROOF, "phase-2")
    os.makedirs(d, exist_ok=True)
    # --- smoke tích hợp gather --inventory-out -> quan --inventory, đối chiếu kho ở tick 0
    log = Log(os.path.join(d, "integration.log"), "Smoke tích hợp gather → file kho → quan (tick 0)")
    sc = os.path.join(tmp, "g.json")
    wj(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100},
                                {"id": "I2", "kind": "bong_sung", "fresh": 100},
                                {"id": "I3", "kind": "bong_sung", "fresh": 100}],
                       "random_fish": False, "monsters": []}})
    inp = os.path.join(tmp, "dock.json")
    wj(inp, {"frames": [{"tick": 0, "interact": True}]})
    kho = os.path.join(d, "integration.kho.json")
    log.run("chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "600", "--scenario", sc,
            "--inputs", inp, "--out", os.path.join(tmp, "g.jsonl"), "--inventory-out", kho)
    end = events(jl(os.path.join(tmp, "g.jsonl")), "gather_end")[0]["data"]
    with open(kho, encoding="utf-8") as f:
        file_items = json.load(f)["items"]
    log.check("gather_end docked, inventory khớp file kho (fresh ±0.01)", end["reason"] == "docked" and same_items(end["inventory"]["items"], file_items),
              json.dumps(file_items, ensure_ascii=False))
    qout = os.path.join(d, "integration.quan.jsonl")
    log.run("chonoi.headless", "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", kho, "--out", qout)
    snap0 = jl(qout)[0]
    log.check("snapshot quán tick 0: stock khớp file (id, kind chính xác; fresh ±0.01)", snap0["tick"] == 0 and same_items(snap0["stock"], file_items))
    ok &= log.save()

    # --- day --days 1 (≤ 22.200 tick, ≤ 20 s) và chuỗi pha
    log = Log(os.path.join(d, "day-1.log"), "day --days 1: chuỗi pha, kết thúc khi Shop đóng")
    out = os.path.join(tmp, "d1.jsonl")
    _, dt = log.run("chonoi.headless", "--mode", "day", "--seed", "1", "--days", "1", "--ticks", "22200", "--out", out)
    rows = jl(out)
    seq = [(r["tick"], r["phase"], r["name"]) for r in events(rows)
           if r["name"] in ("day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")]
    for s in seq:
        log.note(f"  tick {s[0]:>5}  phase={s[1]:<6} {s[2]}")
    e = rows[-1]
    log.check("end: reason days_complete, days_completed 1", e["reason"] == "days_complete" and e["days_completed"] == 1,
              f"ticks={e['ticks']}")
    log.check("một Ngày ≤ 22.200 tick và chạy ≤ 20 s", e["ticks"] <= 22200 and dt <= 20, f"{e['ticks']} tick, {dt:.2f} s")
    log.check("day_plan D1 đúng ticket", events(rows, "day_plan")[0]["data"] ==
              {"dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, "ingredients": {"ca_loc": 3, "bong_sung": 6}})
    ok &= log.save()

    # --- nâng cấp mua Ngày 1 có hiệu lực từ Ngày 2
    log = Log(os.path.join(d, "day-upgrade.log"), "Shop: mua oxygen Ngày 1 → áp dụng từ Ngày 2")
    sc2 = os.path.join(tmp, "up.json")
    wj(sc2, {"day": {"money": 200, "earned": 200}})
    f2 = os.path.join(tmp, "up_in.json")
    wj(f2, {"frames": [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                       {"tick": 10801, "buy": "oxygen"}, {"tick": 10802, "shop_done": True},
                       {"tick": 10803, "shop_done": False}]})
    out = os.path.join(tmp, "up.jsonl")
    log.run("chonoi.headless", "--mode", "day", "--seed", "1", "--days", "2", "--ticks", "11000",
            "--scenario", sc2, "--inputs", f2, "--out", out, "--snapshot-every", "1")
    rows = jl(out)
    bought = events(rows, "bought")
    log.check("bought oxygen cấp 1 giá 200", bought and bought[0]["data"] == {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0},
              json.dumps(bought[0]["data"] if bought else None))
    shop_snaps = [r for r in rows if r["type"] == "snapshot" and r["phase"] == "shop" and r["day"] == 1]
    log.check("Shop Ngày 1: upgrades có oxygen 1, active_upgrades chưa đổi",
              shop_snaps and shop_snaps[-1]["upgrades"] == {"oxygen": 1} and shop_snaps[-1]["active_upgrades"] == {})
    g2 = [r for r in rows if r["type"] == "snapshot" and r.get("day") == 2 and r["phase"] == "gather"]
    log.check("Ngày 2: active_upgrades oxygen 1, oxygen_max_ticks 2700",
              g2 and g2[0]["active_upgrades"] == {"oxygen": 1} and g2[0]["player"]["oxygen_max_ticks"] == 2700,
              f"oxygen_max_ticks={g2[0]['player']['oxygen_max_ticks'] if g2 else None}")
    ok &= log.save()
    return ok


def phase3(tmp):
    ok = True
    d = os.path.join(PROOF, "phase-3")
    os.makedirs(d, exist_ok=True)
    log = Log(os.path.join(d, "spoiled-threshold.log"), "Ngưỡng ươn: scenario mẫu của TICKET-03, một bước")
    sc = os.path.join(tmp, "sp.json")
    wj(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}], "random_fish": False, "monsters": []}})
    out = os.path.join(tmp, "sp.jsonl")
    log.run("chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--out", out)
    sp = events(jl(out), "spoiled")
    want = {"type": "event", "tick": 1, "phase": "gather", "name": "spoiled",
            "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}
    log.check("event spoiled đúng dòng mẫu của ticket", sp == [want], json.dumps(sp, ensure_ascii=False))
    ok &= log.save()

    log = Log(os.path.join(d, "handoff.log"), "Bàn giao kho cá thể qua file (fresh 100, cập bến frame 0, quan --ticks 0)")
    sc = os.path.join(tmp, "h.json")
    wj(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}], "random_fish": False, "monsters": []}})
    inp = os.path.join(tmp, "dock.json")
    wj(inp, {"frames": [{"tick": 0, "interact": True}]})
    kho = os.path.join(d, "handoff.kho.json")
    log.run("chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "10", "--scenario", sc,
            "--inputs", inp, "--out", os.path.join(tmp, "h.jsonl"), "--inventory-out", kho)
    with open(kho, encoding="utf-8") as f:
        items = json.load(f)["items"]
    log.check("file kho sau 1 lần hao ở gather: fresh = 100 − 0.5/60", len(items) == 1 and abs(items[0]["fresh"] - (100 - 0.5 / 60)) < 0.01,
              json.dumps(items, ensure_ascii=False))
    out = os.path.join(tmp, "hq.jsonl")
    log.run("chonoi.headless", "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", kho, "--out", out)
    st = jl(out)[0]["stock"]
    log.check("snapshot quán tick 0 khớp chính xác id/kind/fresh", [(s["id"], s["kind"]) for s in st] == [(i["id"], i["kind"]) for i in items]
              and all(abs(a["fresh"] - b["fresh"]) <= 0.01 for a, b in zip(st, items)))
    old = os.path.join(tmp, "old.json")
    wj(old, {"items": {"ca_loc": 1}})
    log.run("chonoi.headless", "--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", old,
            "--out", os.path.join(tmp, "o.jsonl"), expect=2)
    log.check("file kho đếm kiểu v1.0 bị từ chối (mã 2)", True)
    ok &= log.save()

    log = Log(os.path.join(d, "day-ids.log"), "day --days 2: id cá thể tăng xuyên pha và Ngày")
    sc = os.path.join(tmp, "di.json")
    wj(sc, {"gather": {"hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100}], "random_fish": False}})
    out = os.path.join(tmp, "di.jsonl")
    log.run("chonoi.headless", "--mode", "day", "--seed", "1", "--days", "2", "--ticks", "11500",
            "--scenario", sc, "--inputs", inp, "--out", out)
    rows = jl(out)
    d1 = [r for r in rows if r["type"] == "snapshot" and r.get("day") == 1 and r["phase"] == "gather"][0]["hold"]
    d2 = [r for r in rows if r["type"] == "snapshot" and r.get("day") == 2 and r["phase"] == "gather"][0]["hold"]
    log.check("Ngày 1 giữ id mẫu, Ngày 2 cấp id mới", [h["id"] for h in d1] == ["I1"] and d2 and d2[0]["id"] != "I1",
              f"Ngày 1 {[h['id'] for h in d1]}, Ngày 2 {[h['id'] for h in d2]}")
    ok &= log.save()
    return ok


def phase4(tmp, skip_bench):
    ok = True
    d = os.path.join(PROOF, "phase-4")
    os.makedirs(d, exist_ok=True)
    log = Log(os.path.join(d, "bench.log"), "bench_cmd --seed 42 --duration 30")
    bench = os.path.join(d, "bench.json")
    if skip_bench and os.path.exists(bench):
        log.note("(bỏ chạy lại, giữ bench.json có sẵn)")
    else:
        log.run("chonoi.bench", "--seed", "42", "--duration", "30", "--out", bench)
    with open(bench, encoding="utf-8") as f:
        b = json.load(f)
    log.note(json.dumps(b))
    log.check("đủ 5 trường", set(b) == {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
    log.check("mốc báo cáo avg ≥ 60, 1% low ≥ 30, load ≤ 10 s", b["avg_fps"] >= 60 and b["p1_low_fps"] >= 30 and b["load_ms"] <= 10000,
              "đo phía Python (sim + snapshot + JSON), không gồm vẽ canvas")
    ok &= log.save()

    log = Log(os.path.join(d, "soak.log"), "soak_cmd --seed 7 --days 10 (chạy 2 lần, so tính lặp)")
    s1, s2 = os.path.join(d, "soak.json"), os.path.join(tmp, "soak2.json")
    log.run("chonoi.soak", "--seed", "7", "--days", "10", "--out", s1)
    log.run("chonoi.soak", "--seed", "7", "--days", "10", "--out", s2)
    a, c = [json.load(open(p, encoding="utf-8")) for p in (s1, s2)]
    log.check("days_completed = days = 10, crashes = 0", a["days_completed"] == a["days"] == 10 and a["crashes"] == 0)
    log.check("results[] có 10 mục day/earned/reputation/score", [r["day"] for r in a["results"]] == list(range(1, 11)))
    a.pop("duration_s"), c.pop("duration_s")
    log.check("hai lần chạy giống nhau ở trường gameplay", a == c)
    ok &= log.save()

    log = Log(os.path.join(d, "leaderboard.log"), "Mở rộng leaderboard: 5 Ngày chuẩn → 1 mục, xuất bảng qua run_cmd")
    store = os.path.join(tmp, "store.json")
    log.run("chonoi.headless", "--mode", "day", "--seed", "42", "--days", "5", "--ticks", "120000",
            "--snapshot-every", "5000", "--out", os.path.join(tmp, "lb.jsonl"), "--leaderboard", store, "--player-name", "Út Sen")
    exp = os.path.join(d, "leaderboard.export.json")
    log.run("chonoi.live", "--mode", "gather", "--export-leaderboard", exp, "--leaderboard", store)
    with open(exp, encoding="utf-8") as f:
        e = json.load(f)
    log.note(json.dumps(e, ensure_ascii=False))
    log.check("đúng một mục, days_completed 5, seed 42", len(e["entries"]) == 1 and e["entries"][0]["days_completed"] == 5
              and e["entries"][0]["seed"] == 42)
    log.run("chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "1", "--out", os.path.join(tmp, "x.jsonl"),
            "--leaderboard", store, "--player-name", "A", expect=2)
    log.check("sai mode → mã 2", True)
    ok &= log.save()
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-bench", action="store_true")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="chonoi-proof-")
    try:
        ok = phase2(tmp) & phase3(tmp) & phase4(tmp, a.skip_bench)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
