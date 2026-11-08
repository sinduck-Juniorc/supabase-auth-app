import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("capture", Path(__file__).resolve().parents[1] / "tools/capture_serial.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def test_missing_and_malformed(self):
        for value in (b"", b"\xff", b"[]", b"{}", b"null", b"x" * 1025,
                      b'{"event":"status","uptime_ms":1,"node_id":1,"role":"diagnostic","value":NaN}',
                      b'{"event":"=invalid","uptime_ms":1,"node_id":1,"role":"diagnostic"}'):
            self.assertIsNone(capture.parse_record(value))

    def test_real_record_schema_and_missing_values(self):
        # 파서 단위 테스트 입력이며 실물 수신 결과가 아니다.
        data = {"event": "received_virtual", "uptime_ms": 100, "node_id": 1,
                "role": "seeker", "rssi_dbm": -75, "gnss_quality": None, "battery_soc": None}
        self.assertEqual(capture.parse_record(json.dumps(data).encode()), data)
        self.assertIsNone(capture.parse_record(json.dumps({**data, "node_id": True}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "uptime_ms": -1}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "role": "unknown"}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "rssi_dbm": "=invalid"}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "rssi_dbm": float("inf")}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "rssi_dbm": 10 ** 500}).encode()))
        self.assertIsNone(capture.parse_record(json.dumps({**data, "firmware": "=invalid"}).encode()))


if __name__ == "__main__":
    unittest.main()
