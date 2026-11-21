"""Điểm vào headless: python3 -m chonoi.headless --mode gather|quan|day ..."""

import argparse
import math
import os
import sys

from . import leaderboard
from .contract import load_contract
from .errors import BadInput
from .inputs import load_frames
from .inventory import read_inventory
from .runner import run
from .scenario import load_scenario


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.headless")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--ticks", required=True, type=_int("ticks"))
    p.add_argument("--out", required=True)
    p.add_argument("--scenario")
    p.add_argument("--inputs")
    p.add_argument("--inventory")
    p.add_argument("--inventory-out", dest="inventory_out")
    p.add_argument("--days", type=_int("days"), default=1)
    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)
    # mở rộng leaderboard: cặp cờ chỉ dùng với day
    p.add_argument("--leaderboard")
    p.add_argument("--player-name", dest="player_name")
    a = p.parse_args(argv)
    try:
        if a.ticks < 0:
            raise BadInput("--ticks phải >= 0")
        if a.snapshot_every <= 0:
            raise BadInput("--snapshot-every phải > 0")
        if a.mode != "day" and a.days != 1:
            # argparse default 1; only error if user passed --days with non-day mode
            pass
        if a.mode == "day":
            if not (1 <= a.days <= 5):
                raise BadInput("--days phải trong [1, 5]")
            if a.inventory or a.inventory_out:
                raise BadInput("--inventory/--inventory-out không dùng với day")
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        if (a.leaderboard is None) != (a.player_name is None):
            raise BadInput("--leaderboard và --player-name phải đi cùng nhau")
        if a.leaderboard is not None:
            if a.mode != "day":
                raise BadInput("--leaderboard chỉ dùng với --mode day")
            leaderboard.validate_name(a.player_name)
            leaderboard.load(a.leaderboard)  # store hỏng -> mã 2 trước khi chạy
        outs = [x for x in (a.out, a.inventory_out, a.leaderboard) if x]
        ins = [x for x in (a.scenario, a.inputs, a.inventory) if x]
        paths = [os.path.abspath(x) for x in outs + ins]
        if len(set(paths)) != len(paths):
            raise BadInput("các đường dẫn đầu vào/đầu ra phải khác nhau")
        contract = load_contract()
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        frames = load_frames(a.inputs)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and isinstance(scenario, dict) and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        sim = run(a.mode, tuning, scenario, a.seed, frames, a.ticks, a.out, a.snapshot_every,
                  inventory=inventory, inventory_out=a.inventory_out, days=a.days)
        # Ghi đúng một mục khi chạy đủ 5 Ngày chuẩn, không scenario, reason days_complete.
        if (a.leaderboard and a.days == 5 and a.scenario is None and sim.done
                and sim.reason == "days_complete"):
            mult = tuning["score"]["reputation_multiplier"]
            score = sim.earned + mult * math.floor(sim.reputation)
            leaderboard.record(a.leaderboard, a.player_name, score,
                               getattr(sim, "days_completed", a.days), a.seed)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
