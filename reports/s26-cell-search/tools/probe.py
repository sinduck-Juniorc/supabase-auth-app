"""S26+ 읽기 전용 사전 진단. 기지국 탐색이나 위치 주입을 실행하지 않는다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

PERMISSIONS = ('MODIFY_PHONE_STATE', 'NETWORK_SCAN', 'LOCATION_HARDWARE',
               'ACCESS_FINE_LOCATION')
COMMANDS = [
    ('연결 상태', ['get-state']),
    *[(prop, ['shell', 'getprop', prop]) for prop in (
        'ro.product.manufacturer', 'ro.product.model', 'ro.build.version.release',
        'ro.build.version.sdk', 'ro.build.version.security_patch',
        'ro.build.display.id', 'ro.build.version.oneui')],
    ('shell 권한', ['shell', 'dumpsys', 'package', 'com.android.shell']),
    ('전화 명령 도움말', ['shell', 'cmd', 'phone', 'help']),
    ('위치 명령 도움말', ['shell', 'cmd', 'location', 'help']),
]

def permission_observations(text):
    """요청 목록과 실제 granted 기록을 구분. 누락/상충은 알 수 없음."""
    result = {}
    for permission in PERMISSIONS:
        matches = re.findall(r'android\.permission\.' + permission
                             + r':\s*granted=(true|false)\b', text)
        values = set(matches)
        result[permission] = (next(iter(values)) == 'true') if len(values) == 1 else None
    return result

def run_command(argv, runner=subprocess.run):
    try:
        p = runner(argv, capture_output=True, text=True, encoding='utf-8',
                   errors='replace', timeout=15, check=False)
        return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                'status': '조회됨' if p.returncode == 0 else '명령 오류'}
    except subprocess.TimeoutExpired:
        return {'returncode': None, 'stdout': '', 'stderr': '15초 시간 초과',
                'status': '시간 초과'}
    except OSError as e:
        return {'returncode': None, 'stdout': '', 'stderr': str(e),
                'status': '실행 불가'}

def collect(adb, serial, runner=subprocess.run):
    records = []
    for label, command in COMMANDS:
        result = run_command([adb, '-s', serial, *command], runner)
        # 기기 선택 식별자는 저장하지 않는다.
        result['stderr'] = result['stderr'].replace(serial, '[기기 식별자 생략]')
        result['stdout'] = result['stdout'].replace(serial, '[기기 식별자 생략]')
        records.append({'label': label, 'command': command, **result})
        if label == '연결 상태' and (result['returncode'] != 0 or
                                      result['stdout'].strip() != 'device'):
            break
    permission_record = next((r for r in records if r['label'] == 'shell 권한'), {})
    text = permission_record.get('stdout', '') if permission_record.get('returncode') == 0 else ''
    return {'schema': 1, 'captured_utc': datetime.now(timezone.utc).isoformat(),
            'kind': '읽기 전용 권한·버전 진단', 'records': records,
            'observed_shell_grants': permission_observations(text),
            'binder_call_verified': False, 'gnss_injection_verified': False,
            'cell_search_improvement_measured': False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb', default='adb', help='adb 또는 adb.exe 경로')
    p.add_argument('--serial', help='adb devices에 표시된 선택 기기 식별자')
    p.add_argument('--out', type=Path, default=Path('s26-capabilities.json'))
    p.add_argument('--plan', action='store_true', help='실행할 읽기 명령만 표시')
    args = p.parse_args()
    if args.plan:
        print(json.dumps(COMMANDS, ensure_ascii=False, indent=2)); return 0
    if not args.serial:
        p.error('진단할 기기를 --serial로 지정하세요. --plan은 기기 없이 실행됩니다.')
    if args.out.exists():
        p.error('출력 파일이 이미 있습니다. 새 --out 경로를 지정하세요.')
    report = collect(args.adb, args.serial)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    ok = len(report['records']) == len(COMMANDS) and all(
        r['returncode'] == 0 for r in report['records'])
    print(f'진단 기록: {args.out} / 기지국 탐색 개선 실측: 미실행')
    return 0 if ok else 2

if __name__ == '__main__':
    raise SystemExit(main())
