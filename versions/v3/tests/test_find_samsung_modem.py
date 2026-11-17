import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest


path = Path(__file__).resolve().parents[1] / "tools" / "find_samsung_modem.py"
spec = importlib.util.spec_from_file_location("find_samsung_modem", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def port(device, description, vid=None, pid=None, hwid=""):
    return SimpleNamespace(device=device, description=description, vid=vid, pid=pid, hwid=hwid)


class PortFilterTests(unittest.TestCase):
    def test_exact_modem_only_and_no_identifiers_returned(self):
        ports = [port("COM4", "Bluetooth", hwid="private"),
                 port("COM3", "SAMSUNG Mobile USB Modem", 0x04E8, 0x6860,
                      "USB serial=private"),
                 port("COM8", "SAMSUNG Mobile USB Composite Device", 0x04E8, 0x6860)]
        self.assertEqual(probe.candidates(ports), ["COM3"])

    def test_hwid_fallback_and_numeric_sort(self):
        ports = [port("COM12", "Samsung USB Modem", hwid="USB VID_04E8&PID_6860"),
                 port("COM2", "Samsung USB Modem", hwid="USB VID_04E8&PID_6860")]
        self.assertEqual(probe.candidates(ports), ["COM2", "COM12"])

    def test_rejects_other_vendor_and_non_com_name(self):
        ports = [port("COM3", "Samsung USB Modem", 0x1234, 0x6860),
                 port("private-path", "Samsung USB Modem", 0x04E8, 0x6860)]
        self.assertEqual(probe.candidates(ports), [])


if __name__ == "__main__":
    unittest.main()
