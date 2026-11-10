"""CSQ 고정 질의와 응답 해석의 모의 시험."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import csq_probe as probe
from test_at_probe import FakePort


class CsqTests(unittest.TestCase):
    def collect(self, data, failure=None, written=7):
        port = FakePort(data, failure, written)
        r = probe.collect(lambda **kw: port, 'COM3', clock=lambda: port.now)
        self.assertEqual(port.writes, [] if failure == 'open' else [b'AT+CSQ\r'])
        self.assertEqual(port.events[-1], 'close')
        return r

    def test_signal_codes_and_echo(self):
        r = self.collect(b'AT+CSQ\r+CSQ: 20,99\rOK\r')
        self.assertTrue(r['signal_valid'])
        self.assertEqual(r['signal_codes']['rssi'], dict(code=20, known=True))
        self.assertFalse(r['signal_codes']['ber']['known'])

    def test_boundaries_and_unknown(self):
        for value in (0, 31, 99):
            r = self.collect(('+csq : %d,7\rOK\r' % value).encode())
            self.assertTrue(r['signal_valid'])
            self.assertEqual(r['signal_codes']['rssi']['known'], value != 99)

    def test_invalid_ranges_format_and_duplicates(self):
        for line in (b'+CSQ: 32,0', b'+CSQ: 20,8', b'+CSQ: -1,0',
                     b'+CSQ: 20,1,2', b'+CSQ: private',
                     b'+CSQ: 20,0\r+CSQ: 21,0'):
            r = self.collect(line + b'\rOK\r')
            self.assertFalse(r['signal_valid'])
            self.assertNotIn('private', json.dumps(r))

    def test_error_case_insensitive(self):
        for data in (b'ERROR\r', b'+CME Error : private\rOK\r'):
            r = self.collect(data)
            self.assertEqual(r['status'], 'error_response')
            self.assertFalse(r['signal_valid'])
            self.assertNotIn('private', json.dumps(r))

    def test_ok_without_data_and_timeout(self):
        self.assertFalse(self.collect(b'OK\r')['signal_valid'])
        self.assertEqual(self.collect(b'+CSQ: 20,0\rOK')['status'], 'timeout')

    def test_io_partial_and_close_errors(self):
        for failure in ('open', 'write', 'read', 'close'):
            r = self.collect(b'+CSQ: 20,0\rOK\r', failure)
            self.assertEqual(r['status'], 'close_error' if failure == 'close' else 'io_error')
        self.assertEqual(self.collect(b'', written=1)['status'], 'partial_write')

    def test_limit(self):
        port = FakePort(b'x' * 5000, written=7)
        r = probe.collect(lambda **kw: port, 'COM3', clock=lambda: 0)
        self.assertEqual(r['status'], 'receive_limit')

    def test_plan(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(probe.main(['--plan']), 0)
        self.assertEqual(json.loads(output.getvalue())['command_hex'], '41 54 2b 43 53 51 0d')


if __name__ == '__main__':
    unittest.main()
