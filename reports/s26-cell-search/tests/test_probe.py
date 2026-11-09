"""합성 입력으로 진단기의 오판 방지를 검사한다. S26 실물 시험이 아니다."""
import sys
from pathlib import Path
import subprocess
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import probe

class ProbeTests(unittest.TestCase):
    def test_requested_permission_is_not_granted(self):
        self.assertIsNone(probe.permission_observations(
            'requested permissions: android.permission.MODIFY_PHONE_STATE')['MODIFY_PHONE_STATE'])

    def test_grant_deny_and_conflict(self):
        text = ('android.permission.MODIFY_PHONE_STATE: granted=true\n'
                'android.permission.LOCATION_HARDWARE: granted=false\n'
                'android.permission.NETWORK_SCAN: granted=true\n'
                'android.permission.NETWORK_SCAN: granted=false')
        values = probe.permission_observations(text)
        self.assertIs(values['MODIFY_PHONE_STATE'], True)
        self.assertIs(values['LOCATION_HARDWARE'], False)
        self.assertIsNone(values['NETWORK_SCAN'])

    def test_offline_stops_and_redacts(self):
        calls=[]
        def runner(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 1, '', 'device fixture-serial offline')
        result=probe.collect('adb', 'fixture-serial', runner)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('fixture-serial', str(result))
        self.assertIsNone(result['observed_shell_grants']['MODIFY_PHONE_STATE'])
        self.assertFalse(result['cell_search_improvement_measured'])

    def test_timeout_and_missing_executable(self):
        for error in [subprocess.TimeoutExpired('adb', 15), FileNotFoundError('adb 없음')]:
            def runner(*args, **kwargs): raise error
            self.assertIsNone(probe.run_command(['adb'], runner)['returncode'])

    def test_all_success_is_still_not_injection(self):
        def runner(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0,
                'device\n' if argv[-1] == 'get-state' else
                'android.permission.MODIFY_PHONE_STATE: granted=true', '')
        result=probe.collect('adb', 'fixture-serial', runner)
        self.assertEqual(len(result['records']),len(probe.COMMANDS))
        self.assertFalse(result['gnss_injection_verified'])
        self.assertFalse(result['binder_call_verified'])

if __name__ == '__main__': unittest.main()
