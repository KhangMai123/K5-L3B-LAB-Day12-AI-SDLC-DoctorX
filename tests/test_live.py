"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveServerTest(unittest.TestCase):
    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(st["menu"], tuning["menu"], "HUD quán cần thực đơn")
            self.assertEqual(st["meta"], tuning["gather"])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            self.assertIn(b"drawShop", html)
            code, png = _get(base + "/assets/ca_loc.png")
            self.assertEqual(code, 200)
            self.assertTrue(png.startswith(b"\x89PNG"), "ảnh asset phải là PNG thật")
            for bad in ("/assets/../live.py", "/assets/%2e%2e/live.py", "/assets/khong_co.png", "/assets/x.py"):
                with self.assertRaises(urllib.error.HTTPError, msg=bad) as cm:
                    _get(base + bad)
                self.assertEqual(cm.exception.code, 404, bad)
                cm.exception.close()
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())

    def test_day_mode_phase_and_shop_input(self):
        tuning = load_contract()["tuning"]
        # Scenario ngắn: gather hết giờ gần như ngay → quan → shop
        scenario = {
            "gather": {"time_left_ticks": 3, "hold": []},
            "quan": {"time_left_ticks": 3, "stock": []},
            "day": {"money": 300, "earned": 300},
        }
        server = LiveServer(LiveGame("day", tuning, scenario, 1, days=1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            st = json.loads(_get(base + "/state")[1])
            self.assertEqual(st["mode"], "day")
            self.assertEqual(st["day"], 1)
            self.assertIn(st["phase"], ("gather", "quan", "shop"))
            # chờ sang shop (gather/quan ngắn ở 60 tick/s)
            deadline = time.time() + 4
            while time.time() < deadline:
                st = json.loads(_get(base + "/state")[1])
                if st["phase"] == "shop" or st.get("finished"):
                    break
                time.sleep(0.02)
            self.assertEqual(st["phase"], "shop", "day phải vào shop sau gather/quan ngắn")
            self.assertEqual(st["meta"], tuning["shop"])
            self.assertIn("upgrades", st)
            money_before = st["money"]
            self.assertEqual(_post(base + "/input", {"buy": "oxygen"}), 200)
            deadline = time.time() + 1
            bought = False
            while time.time() < deadline:
                st = json.loads(_get(base + "/state")[1])
                if st.get("upgrades", {}).get("oxygen", 0) >= 1 or st["money"] < money_before:
                    bought = True
                    break
                time.sleep(0.02)
            self.assertTrue(bought, "buy oxygen phải trừ tiền / tăng cấp")
            self.assertEqual(_post(base + "/input", {"shop_done": True}), 200)
            deadline = time.time() + 2
            while time.time() < deadline:
                st = json.loads(_get(base + "/state")[1])
                if st.get("finished"):
                    break
                time.sleep(0.02)
            self.assertTrue(st.get("finished"), "shop_done phải kết thúc 1 Ngày")
            self.assertEqual(st.get("reason"), "days_complete")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
