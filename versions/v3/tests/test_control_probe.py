"""합성 ADB 응답 시험이며 실기기 검증이 아니다."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import control_probe as probe


class ControlProbeTests(unittest.TestCase):
    def runner(self, argv, **kwargs):
        command = argv[3:]
        value = 'private-raw-output fixture-serial'
        if command == ['get-state']:
            value = 'device'
        elif command[:3] == ['shell', 'dumpsys', 'package']:
            package = command[-1]
            value = f'Package [{package}] (fixture):\n'
            value += 'android.permission.ACCESS_FINE_LOCATION: granted=true\n'
            if package == 'com.android.shell':
                value += 'android.permission.LOCATION_HARDWARE: granted=true\n'
                value += 'android.permission.MODIFY_PHONE_STATE: granted=true\n'
            else:
                value += 'requested permissions: android.permission.LOCATION_HARDWARE\n'
        elif command == ['shell', 'id', '-u']:
            value = '2000'
        elif command[:2] == ['shell', 'getprop']:
            value = ''
        return subprocess.CompletedProcess(argv, 0, value, 'private-error fixture-serial')

    def test_shell_grants_do_not_transfer_to_app(self):
        report = probe.collect('adb', 'fixture-serial', self.runner)
        self.assertEqual(report['shell_uid'], 2000)
        self.assertIn('충족·호출 미검증', report['shell_paths']['location_cache_injection'])
        self.assertEqual(report['v3_paths']['location_cache_injection'], '권한 충족 미확인')
        self.assertIsNone(report['observed_v3_grants']['LOCATION_HARDWARE'])
        for paths in (report['shell_paths'], report['v3_paths']):
            self.assertFalse(paths['binder_call_verified'])
            self.assertFalse(paths['gnss_hal_injection_verified'])
            self.assertFalse(paths['cell_search_improvement_measured'])
            self.assertEqual(paths['carrier_privileges'], '미검증')

    def test_raw_dumps_help_errors_and_selector_are_not_saved(self):
        encoded = json.dumps(probe.collect('adb', 'fixture-serial', self.runner))
        for private in ('fixture-serial', 'private-raw-output', 'private-error'):
            self.assertNotIn(private, encoded)

    def test_missing_package_is_unknown_even_with_granted_string(self):
        def runner(argv, **kwargs):
            if argv[3:6] == ['shell', 'dumpsys', 'package']:
                return subprocess.CompletedProcess(argv, 0,
                    'android.permission.LOCATION_HARDWARE: granted=true', '')
            return self.runner(argv, **kwargs)
        report = probe.collect('adb', 'fixture-serial', runner)
        self.assertIsNone(report['observed_shell_grants']['LOCATION_HARDWARE'])

    def test_conflicting_users_are_unknown(self):
        text = ('android.permission.ACCESS_FINE_LOCATION: granted=true\n'
                'android.permission.ACCESS_FINE_LOCATION: granted=false')
        self.assertIsNone(probe.base.permission_observations(text)['ACCESS_FINE_LOCATION'])

    def test_offline_stops_before_shell(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, 'offline', '')
        report = probe.collect('adb', 'fixture-serial', runner)
        self.assertEqual(len(calls), 1)
        self.assertFalse(report['records'][0]['connected'])

    def test_missing_adb_is_recorded_without_raw_error(self):
        def runner(*args, **kwargs):
            raise FileNotFoundError('private-path fixture-serial')
        report = probe.collect('missing-adb', 'fixture-serial', runner)
        self.assertEqual(len(report['records']), 1)
        self.assertIsNone(report['records'][0]['returncode'])
        self.assertNotIn('private-path', json.dumps(report))

    def test_command_allowlist_remains_readonly(self):
        allowed = {('get-state',), ('shell', 'id', '-u'),
                   ('shell', 'dumpsys', 'package', 'com.android.shell'),
                   ('shell', 'dumpsys', 'package', probe.PACKAGE),
                   ('shell', 'cmd', 'phone', 'help'),
                   ('shell', 'cmd', 'location', 'help')}
        properties = {'ro.product.manufacturer', 'ro.product.model',
                      'ro.build.version.release', 'ro.build.version.sdk',
                      'ro.build.version.security_patch', 'ro.build.display.id',
                      'ro.build.version.oneui'}
        allowed.update(('shell', 'getprop', prop) for prop in properties)
        self.assertEqual({tuple(command) for _, command in probe.COMMANDS}, allowed)

    def test_plan_and_existing_file_do_not_run_adb(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(probe.main(['--plan', '--adb', 'does-not-exist']), 0)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'existing.json'
            output.write_text('preserved', encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                probe.main(['--serial', 'fixture', '--out', str(output)])
            self.assertEqual(output.read_text(), 'preserved')


if __name__ == '__main__':
    unittest.main()
