"""TICKET-04 mục 1: bench_cmd tạo bench.json đủ 5 trường, đúng công thức."""

import json
import subprocess
import sys
import unittest

from helpers import ROOT, Workdir


class BenchP4(unittest.TestCase):
    def test_bench_json_fields_and_formulas(self):
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", "1",
                                "--warmup", "0.2", "--out", out], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                b = json.load(f)
        self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertIsInstance(b["frames"], int)
        self.assertGreater(b["frames"], 0)
        self.assertGreaterEqual(b["measured_s"], 1.0)
        self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], places=6)
        self.assertLessEqual(b["p1_low_fps"], b["avg_fps"])  # khung chậm nhất không nhanh hơn trung bình
        self.assertGreaterEqual(b["load_ms"], 0)


if __name__ == "__main__":
    unittest.main()
