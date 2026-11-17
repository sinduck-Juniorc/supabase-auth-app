"""CSQ 고정 질의와 응답 해석의 모의 시험."""
import contextlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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

    def test_numeric_error_meaning(self):
        r = self.collect(b'+CME ERROR: 4\r')
        self.assertEqual(r['cme_error']['numeric_code'], 4)
        self.assertEqual(r['cme_error']['standard_meaning'], 'operation_not_supported')

    def test_exact_verbose_error(self):
        r = self.collect(b'+CME Error: Operation Not Allowed\r')
        self.assertEqual(r['cme_error']['standard_meaning'], 'operation_not_allowed')

    def test_vendor_wording_is_only_a_cue(self):
        r = self.collect(b'+CME Error:Not Support(private-serial)\r')
        self.assertIsNone(r['cme_error']['standard_meaning'])
        self.assertEqual(r['cme_error']['wording_cues'], ['not_supported_wording'])
        self.assertNotIn('private-serial', json.dumps(r))

    def test_unknown_error_and_long_identifier_not_retained(self):
        for detail in (b'123456789012345', b'private-serial', b'99999'):
            r = self.collect(b'+CME ERROR: ' + detail + b'\r')
            self.assertIsNone(r['cme_error']['numeric_code'])
            self.assertNotIn(detail.decode(), json.dumps(r))

    def test_unmapped_numeric_code_preserved_without_invented_meaning(self):
        r = self.collect(b'+CME ERROR: 515\r')
        self.assertEqual(r['cme_error']['numeric_code'], 515)
        self.assertIsNone(r['cme_error']['standard_meaning'])

    def test_screen_detail_is_separate_from_result(self):
        port = FakePort(b'+CME ERROR: private-serial\r', written=7)
        shown = []
        result = probe.collect(lambda **kw: port, 'COM7', clock=lambda: port.now,
                               detail_sink=shown.append)
        self.assertEqual(shown, [b'+CME ERROR: private-serial'])
        self.assertNotIn('private-serial', json.dumps(result))
        self.assertEqual(port.writes, [b'AT+CSQ\r'])
        self.assertEqual(port.events[-1], 'close')

    def test_screen_render_escapes_controls_and_limits_length(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            probe.show_cme_detail(b'+CME ERROR: private\x1b[31m\x00\tvalue')
        rendered = output.getvalue()
        self.assertIn('private', rendered)
        self.assertIn('\\x1b', rendered)
        self.assertIn('\\x00', rendered)
        self.assertNotIn('\x1b', rendered)
        self.assertNotIn('\x00', rendered)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            probe.show_cme_detail(b'+CME ERROR: ' + b'x' * 300)
        self.assertIn('256바이트 이후 생략', output.getvalue())
        self.assertNotIn('x' * 257, output.getvalue())

    def test_screen_mode_requires_explicit_port_and_console(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                probe.main(['--send-csq-show-cme'])
            with patch.object(probe.sys, 'platform', 'win32'):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        probe.main(['--send-csq-show-cme', '--port', 'COM7'])
            with self.assertRaises(SystemExit):
                probe.main(['--send-csq-show-cme', '--port', 'COM7', '--out', 'x.json'])

    def test_screen_mode_writes_no_result_file(self):
        class Console(io.StringIO):
            def isatty(self):
                return True

        port = FakePort(b'+CME ERROR: private-serial\r', written=7)
        console = Console()
        fake_serial = SimpleNamespace(Serial=lambda **kw: port)
        with patch.object(probe.sys, 'platform', 'win32'):
            with patch.object(probe.sys, 'stdout', console):
                with patch.dict(sys.modules, {'serial': fake_serial}):
                    with patch.object(probe.Path, 'open', side_effect=AssertionError('file opened')):
                        self.assertEqual(probe.main(['--send-csq-show-cme', '--port', 'COM7']), 2)
        self.assertEqual(console.getvalue().count('private-serial'), 1)
        self.assertEqual(port.writes, [b'AT+CSQ\r'])
        self.assertEqual(port.events[-1], 'close')


if __name__ == '__main__':
    unittest.main()
