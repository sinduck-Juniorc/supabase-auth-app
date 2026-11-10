"""CESQ 모의 응답 시험. 실제 단말 시험은 별도다."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cesq_probe as probe
from test_at_probe import FakePort


class CesqTests(unittest.TestCase):
    def run_probe(self, response, failure=None, written=8):
        port = FakePort(response, failure, written)
        def factory(**kwargs):
            self.assertIsNone(kwargs['port'])
            self.assertEqual(kwargs, dict(port=None, **probe.SETTINGS))
            return port
        report = probe.collect(factory, 'COM3', clock=lambda: port.now)
        self.assertEqual(port.writes, [] if failure == 'open' else [b'AT+CESQ\r'])
        self.assertEqual(port.events[0], ('open', False, False, 'COM3'))
        self.assertEqual(port.events[-1], 'close')
        return report

    def test_six_fields_unknown_is_not_zero(self):
        r = self.run_probe(b'AT+CESQ\r\n+CESQ: 99,99,255,255,20,45\r\nOK\r')
        self.assertTrue(r['signal_valid'])
        self.assertFalse(r['signal_codes']['rxlev']['known'])
        self.assertEqual(r['signal_codes']['rsrp'], dict(code=45, known=True))
        self.assertNotIn('ss_rsrp', r['signal_codes'])

    def test_nine_fields_and_zero(self):
        r = self.run_probe(b'+CESQ: 0,0,0,0,0,0,126,126,127\rOK\r')
        self.assertTrue(r['signal_valid'])
        self.assertTrue(r['signal_codes']['rsrp']['known'])

    def test_unknown_all_fields(self):
        r = self.run_probe(b'+CESQ: 99,99,255,255,255,255,255,255,255\rOK\r')
        self.assertTrue(r['signal_valid'])
        self.assertTrue(all(not v['known'] for v in r['signal_codes'].values()))

    def test_bad_ranges_counts_and_private_data(self):
        for payload in (b'99,99,255,255,35,45', b'99,99,255,255,20,98',
                        b'1,2,3,4,5,6,7', b'-1,2,3,4,5,6', b'private-serial'):
            r = self.run_probe(b'+CESQ: ' + payload + b'\rOK\r')
            self.assertFalse(r['signal_valid'])
            self.assertEqual(r['malformed_cesq_lines'], 1)
            self.assertNotIn('private', json.dumps(r))

    def test_duplicate_samples_are_ambiguous(self):
        r = self.run_probe(b'+CESQ: 1,2,3,4,5,6\r+CESQ: 1,2,3,4,5,6\rOK\r')
        self.assertFalse(r['signal_valid'])

    def test_ok_without_sample_and_unexpected_urc(self):
        r = self.run_probe(b'+URC: private\rOK\r')
        self.assertFalse(r['signal_valid'])
        self.assertEqual(r['unparsed_lines'], 1)
        self.assertNotIn('private', json.dumps(r))

    def test_error_and_extended_error(self):
        for response in (b'ERROR\r', b'+CME ERROR: private\r'):
            r = self.run_probe(response)
            self.assertEqual(r['status'], 'error_response')
            self.assertFalse(r['signal_valid'])

    def test_partial_line_timeout(self):
        r = self.run_probe(b'+CESQ: 1,2,3,4,5,6\rOK')
        self.assertEqual(r['status'], 'timeout')
        self.assertFalse(r['signal_valid'])

    def test_io_partial_write_close_errors(self):
        for failure in ('open', 'write', 'read', 'close'):
            r = self.run_probe(b'+CESQ: 1,2,3,4,5,6\rOK\r', failure)
            self.assertEqual(r['status'], 'close_error' if failure == 'close' else 'io_error')
        self.assertEqual(self.run_probe(b'', written=2)['status'], 'partial_write')

    def test_limit(self):
        port = FakePort(b'x' * 5000, written=8)
        r = probe.collect(lambda **kw: port, 'COM3', clock=lambda: 0)
        self.assertEqual(r['status'], 'receive_limit')
        self.assertFalse(r['signal_valid'])

    def test_plan(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(probe.main(['--plan']), 0)
        self.assertEqual(json.loads(output.getvalue())['command_hex'], '41 54 2b 43 45 53 51 0d')

    def test_prefix_spacing_and_case(self):
        r = self.run_probe(b'+cesq : 99,99,255,255,20,45\rOK\r')
        self.assertTrue(r['signal_valid'])

    def test_diagnostic_shape_does_not_retain_values_or_words(self):
        r = self.run_probe(b'+CESQ=99,99,255,255,20,45\rPRIVATE123\rOK\r')
        self.assertFalse(r['signal_valid'])
        self.assertTrue(r['unparsed_shapes'][0]['cesq_marker_present'])
        self.assertEqual(r['unparsed_shapes'][1]['shape'], 'XXXXXXX###')
        self.assertNotIn('PRIVATE123', json.dumps(r))
        self.assertNotIn('99,99', json.dumps(r))

    def test_diagnostics_are_bounded(self):
        port = FakePort((b'X' * 140 + b'\r') * 10 + b'OK\r', written=8)
        r = probe.collect(lambda **kw: port, 'COM3', clock=lambda: 0)
        self.assertEqual(len(r['unparsed_shapes']), 8)
        self.assertEqual(len(r['unparsed_shapes'][0]['shape']), 128)
        self.assertTrue(r['unparsed_shapes'][0]['truncated'])


if __name__ == '__main__':
    unittest.main()
