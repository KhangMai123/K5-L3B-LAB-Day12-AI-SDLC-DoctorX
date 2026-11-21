"""Kiểm định game.contract.json, chonoi.contract và CLI headless (exit 0/1/2)."""

import copy
import json
import os
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from helpers import ROOT, Workdir, run_headless


def _contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


class ContractValidation(unittest.TestCase):
    def test_contract_json_has_required_v1_keys_and_values(self):
        c = _contract()
        self.assertEqual(c["contract_version"], "1.0")
        self.assertEqual(c["team"], "doctorx")
        self.assertEqual(c["team_size"], 6)
        for k in ("headless_cmd", "run_cmd", "build_cmd"):
            self.assertIsInstance(c[k], str)
            self.assertTrue(c[k].strip())
        t = c["tuning"]
        self.assertEqual(t["tick_hz"], 60)
        self.assertIsNone(t["quan"]["burn_s"])
        self.assertEqual([s["id"] for s in t["quan"]["stoves"]], ["B1"])
        self.assertEqual([tb["id"] for tb in t["quan"]["tables"]], ["T1"])
        self.assertEqual(
            {k: v["recipe"] for k, v in t["menu"].items()},
            {
                "ca_loc_nuong_trui": {"ca_loc": 1},
                "goi_bong_sung": {"bong_sung": 2},
                "lau_ca_linh_dien_dien": {"ca_linh": 3, "bong_dien_dien": 1},
            },
        )
        load_contract()

    def test_validate_tuning_rejects_out_of_range_and_bad_menu(self):
        base = _contract()["tuning"]
        bad_cases = [
            lambda t: t.__setitem__("tick_hz", 30),
            lambda t: t["gather"].__setitem__("duration_s", 59),
            lambda t: t["gather"].__setitem__("hold_capacity", 31),
            lambda t: t["gather"].__setitem__("ramp_max_ticks", 7),
            lambda t: t["quan"].__setitem__("patience_s", 19),
            lambda t: t["quan"].__setitem__("burn_s", 10),
            lambda t: t["quan"].__setitem__("tip_min_patience_ratio", 0),
            lambda t: t["quan"].__setitem__("left_reputation_delta", 0.1),
            lambda t: t["quan"].__setitem__("first_customer_tick", 0),
            lambda t: t["menu"]["ca_loc_nuong_trui"].__setitem__("recipe", {"ca_linh": 1}),
            lambda t: t["menu"]["goi_bong_sung"].__setitem__("price", 0),
        ]
        for mutate in bad_cases:
            t = copy.deepcopy(base)
            mutate(t)
            with self.assertRaises(BadInput):
                validate_tuning(t)


class CliFlagsAndExitCodes(unittest.TestCase):
    def test_invalid_cli_flags_exit_2_without_creating_out(self):
        with Workdir() as w:
            out = w.path("out.jsonl")
            cases = [
                ("--mode", "gather", "--seed", "abc", "--ticks", "0", "--out", out),
                ("--mode", "gather", "--seed", "1", "--ticks", "-1", "--out", out),
                ("--mode", "gather", "--seed", "1", "--ticks", "0", "--snapshot-every", "0", "--out", out),
                ("--mode", "gather", "--seed", "1", "--ticks", "0", "--snapshot-every", "-5", "--out", out),
                ("--mode", "unknown", "--seed", "1", "--ticks", "0", "--out", out),
                ("--mode", "gather", "--seed", "1", "--ticks", "0", "--out", out, "--unknown-flag", "1"),
            ]
            for args in cases:
                code, err = run_headless(*args)
                self.assertEqual(code, 2, (args, err))
                self.assertFalse(os.path.exists(out), f"created out for invalid args {args}")

    def test_signed_negative_seed_accepted(self):
        with Workdir() as w:
            out = w.path("neg.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "-42", "--ticks", "0", "--out", out)
            self.assertEqual(code, 0, err)
            self.assertTrue(os.path.exists(out))

    def test_input_output_path_collision_exit_2(self):
        with Workdir() as w:
            p = w.path("same.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"frames": []}, f)
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--inputs", p, "--out", p)
            self.assertEqual(code, 2)

    def test_write_error_exit_1(self):
        with Workdir() as w:
            bad_out = os.path.join(w.path("nonexistent_dir"), "out.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--out", bad_out)
            self.assertEqual(code, 1, err)


if __name__ == "__main__":
    unittest.main()
