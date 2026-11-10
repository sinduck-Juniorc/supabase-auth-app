"""모의 직렬 포트 시험. Windows 드라이버/실물 시험을 대체하지 않는다."""
import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import at_probe as probe


class FakePort:
    def __init__(self, response=b'AT\r\r\nOK\r\n', failure=None, written=3):
        self.response, self.failure, self.written = response, failure, written
        self.writes, self.events, self.now = [], [], 0

    def open(self):
        self.events.append(('open', self.dtr, self.rts, self.port))
        if self.failure == 'open':
            raise OSError('private path')

    def reset_input_buffer(self):
        self.events.append('reset_input')

    def write(self, data):
        self.writes.append(data)
        if self.failure == 'write':
            raise TimeoutError('private path')
        return self.written

    def read(self, size):
        self.now += 0.01
        if self.failure == 'read':
            raise OSError('private response')
        result, self.response = self.response[:size], self.response[size:]
        return result

    def close(self):
        self.events.append('close')
        if self.failure == 'close':
            raise OSError('private path')


class AtProbeTests(unittest.TestCase):
    def run_probe(self, port):
        def factory(**kwargs):
            self.assertIsNone(kwargs['port'])
            self.assertEqual(kwargs['timeout'], 0.1)
            self.assertEqual(kwargs['write_timeout'], 1)
            self.assertFalse(kwargs['rtscts'])
            self.assertFalse(kwargs['dsrdtr'])
            self.assertFalse(kwargs['xonxoff'])
            return port
        return probe.collect(factory, 'COM3', clock=lambda: port.now)

    def test_one_command_and_control_lines_before_open(self):
        port = FakePort()
        report = self.run_probe(port)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(port.writes, [b'AT\r'])
        self.assertEqual(port.events, [('open', False, False, 'COM3'), 'reset_input', 'close'])

    def test_error_is_not_success(self):
        self.assertEqual(self.run_probe(FakePort(b'\r\nERROR\r\n'))['status'], 'error_response')

    def test_timeout_echo_partial_and_substrings_are_not_success(self):
        for response in (b'', b'AT\r', b'OK', b'NOTOK\r', b'private data\r'):
            with self.subTest(response=response):
                port = FakePort(response)
                report = self.run_probe(port)
                self.assertEqual(report['status'], 'timeout')
                self.assertTrue(report['closed'])
                self.assertEqual(len(port.writes), 1)
                self.assertNotIn('private', str(report))

    def test_io_failures_close_without_retry(self):
        for stage in ('open', 'write', 'read'):
            with self.subTest(stage=stage):
                port = FakePort(failure=stage)
                report = self.run_probe(port)
                self.assertEqual(report['status'], 'io_error')
                self.assertTrue(report['closed'])
                self.assertEqual(len(port.writes), 0 if stage == 'open' else 1)
                self.assertNotIn('private', str(report))

    def test_partial_write_stops(self):
        port = FakePort(written=1)
        self.assertEqual(self.run_probe(port)['status'], 'partial_write')
        self.assertEqual(port.writes, [b'AT\r'])
        self.assertEqual(port.now, 0)

    def test_close_failure_overrides_ok(self):
        report = self.run_probe(FakePort(failure='close'))
        self.assertEqual(report['status'], 'close_error')
        self.assertEqual(report['terminal_response'], 'OK')
        self.assertFalse(report['closed'])

    def test_receive_limit(self):
        port = FakePort(b'x' * 5000)
        report = probe.collect(lambda **kw: port, 'COM3', clock=lambda: 0)
        self.assertEqual(report['status'], 'receive_limit')
        self.assertEqual(report['bytes_received'], 4096)

    def test_default_and_plan_do_not_need_serial(self):
        for args in ([], ['--plan']):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(args), 0)


if __name__ == '__main__':
    unittest.main()
