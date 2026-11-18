import importlib.util
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


path = Path(__file__).resolve().parents[1] / "tools" / "send_one_hop_digits.py"
spec = importlib.util.spec_from_file_location("send_one_hop_digits", path)
sender = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sender)


class SendOneHopDigitsTests(unittest.TestCase):
    def test_r4_port_filter(self):
        ports = [
            SimpleNamespace(device="COM3", vid=0x2341, pid=0x1002),
            SimpleNamespace(device="com12", vid=0x2341, pid=0x006D),
            SimpleNamespace(device="COM4", vid=0x04E8, pid=0x6860),
            SimpleNamespace(device="COM5", vid=0x2341, pid=0x0069),
        ]
        self.assertEqual(sender.r4_ports(ports), ["COM3", "COM12"])

    def test_four_single_byte_writes_three_seconds_apart(self):
        now = 100
        writes = []

        def sleep(seconds):
            nonlocal now
            now += seconds

        def write(digit):
            writes.append((now, digit))
            sleep(0.25)
            return len(digit)

        clock = SimpleNamespace(monotonic=lambda: now, sleep=sleep)
        with patch.object(sender, "time", clock), redirect_stdout(StringIO()):
            sender.send_digits(SimpleNamespace(write=write))
        self.assertEqual(writes, [(100, b"0"), (103, b"1"), (106, b"0"), (109, b"1")])

    def test_short_write_aborts_without_retry(self):
        connection = Mock()
        connection.write.return_value = 0
        with self.assertRaises(OSError):
            sender.send_digits(connection)
        connection.write.assert_called_once_with(b"0")
