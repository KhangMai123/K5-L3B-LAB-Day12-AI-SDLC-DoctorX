"""Vòng tick (Contract B). Session dùng chung headless và live."""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    if mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    return DaySim(tuning, scenario, streams, ids, days=days)


def _common(sim, tick, sim_tick, phase_tick, tuning, state, day=None):
    mult = tuning["score"]["reputation_multiplier"]
    row = {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }
    if day is not None:
        row["day"] = day
    return row


class Session:
    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        state = "finished" if self.sim.done else ("paused" if getattr(self.sim, "paused", False) else "playing")
        day = getattr(self.sim, "day", None) if self.mode == "day" else None
        phase_tick = getattr(self.sim, "phase_tick", self.sim_tick)
        s = _common(self.sim, self.tick, self.sim_tick, phase_tick, self.tuning, state, day=day)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        events = self.sim.step(inp)
        self.tick += 1
        if not getattr(self.sim, "paused", False) or any(n == "resumed" for n, _ in events):
            # sim_tick tăng khi có gameplay; pause-only bước không tăng (DaySim không tăng phase khi pause)
            if self.mode == "day":
                self.sim_tick = self.tick  # simplified: wall clock for day outer; gameplay tracked in phase_tick
            else:
                self.sim_tick = self.tick
        return self._rows(events)

    def _rows(self, events):
        # day: mỗi event mang (phase, day) lúc phát — event kết thúc mang pha cũ (Test Contract 4.4)
        meta = getattr(self.sim, "event_meta", None) if self.mode == "day" else None
        rows = []
        for i, (name, data) in enumerate(events):
            phase, day = meta[i] if meta else (self.sim.phase, getattr(self.sim, "day", None))
            row = {"type": "event", "tick": self.tick, "phase": phase, "name": name, "data": data}
            if self.mode == "day":
                row["day"] = day
            rows.append(row)
        return rows

    def initial_events(self) -> list:
        """Event của tick 0 (day: day_start → day_plan → phase_start(gather))."""
        take = getattr(self.sim, "take_initial_events", None)
        return self._rows(take()) if take else []

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, getattr(sim, "phase_tick", self.sim_tick),
                        self.tuning, "")["score"]
        row = {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
               "state": "finished" if sim.done else "playing",
               "reason": sim.reason if sim.done else "tick_limit",
               "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}
        if self.mode == "day":
            row["days_completed"] = getattr(sim, "days_completed", 0)
        return row

    def write_inventory_if_done(self, inventory_out):
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # Contract B: snapshot tick 0 là dòng đầu
        for row in sess.initial_events():  # rồi event của tick 0 (day: day_start → day_plan → phase_start)
            w.write(row)
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
