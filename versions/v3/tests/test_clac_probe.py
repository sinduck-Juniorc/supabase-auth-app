"""CLAC 모의 응답 검증이며 실물 지원 여부는 검증하지 않는다."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import clac_probe as probe
from test_at_probe import FakePort


class ClacTests(unittest.TestCase):
    def collect(self, response, failure=None, written=8):
        port = FakePort(response, failure, written)
        report = probe.collect(lambda **kw: port, 'COM3', clock=lambda: port.now)
        self.assertEqual(port.writes, [] if failure == 'open' else [b'AT+CLAC\r'])
        self.assertEqual(port.events[-1], 'close')
        return report

    def test_names_echo_and_duplicates(self):
        report = self.collect(b'AT+CLAC\r\nAT+CREG\r\nAT+CGMI\r\nAT+CREG\r\nOK\r')
        self.assertEqual(report['command_names'], ['AT+CGMI', 'AT+CREG'])
        self.assertTrue(report['list_complete'])

    def test_empty_ok_is_not_a_list(self):
        self.assertFalse(self.collect(b'OK\r')['list_complete'])

    def test_error_and_extended_error(self):
        for response in (b'ERROR\r', b'+CME ERROR: private detail\r'):
            report = self.collect(response)
            self.assertEqual(report['status'], 'error_response')
            self.assertNotIn('private', json.dumps(report))

    def test_raw_values_are_omitted(self):
        report = self.collect(b'AT+CGMI\r+CGSN: private-serial\rATD12345;\rOK\r')
        self.assertEqual(report['unparsed_lines'], 2)
        self.assertFalse(report['list_complete'])
        self.assertNotIn('private-serial', json.dumps(report))

    def test_partial_response_and_timeout(self):
        report = self.collect(b'AT+CGMI\rOK')
        self.assertEqual(report['status'], 'timeout')
        self.assertFalse(report['list_complete'])

    def test_errors_partial_write_and_close_failure(self):
        for failure in ('open', 'write', 'read', 'close'):
            report = self.collect(b'OK\r', failure)
            self.assertEqual(report['status'], 'close_error' if failure == 'close' else 'io_error')
        self.assertEqual(self.collect(b'', written=2)['status'], 'partial_write')

    def test_receive_limit(self):
        port = FakePort(b'x' * 70000, written=8)
        report = probe.collect(lambda **kw: port, 'COM3', clock=lambda: 0)
        self.assertEqual(report['status'], 'receive_limit')
        self.assertFalse(report['list_complete'])

    def test_plan_never_opens_port(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(probe.main(['--plan']), 0)
        self.assertEqual(json.loads(output.getvalue())['command_hex'], '41 54 2b 43 4c 41 43 0d')


if __name__ == '__main__':
    unittest.main()
