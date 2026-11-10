"""V3 제어 경로 사전 확인. 고정된 읽기 명령만 실행하고 원문은 저장하지 않는다."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    's26_readonly_probe', ROOT / 'reports/s26-cell-search/tools/probe.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PACKAGE = 'org.zetamesh.gnss.v3'
COMMANDS = [*base.COMMANDS,
            ('shell UID', ['shell', 'id', '-u']),
            ('V3 권한', ['shell', 'dumpsys', 'package', PACKAGE])]


def path_assessment(grants):
    # 권한 부재로 carrier privilege 경로까지 부정하지 않는다.
    return {
        'location_cache_injection': (
            '권한 기록 충족·호출 미검증' if all(grants.get(p) is True for p in
                ('LOCATION_HARDWARE', 'ACCESS_FINE_LOCATION')) else '권한 충족 미확인'),
        'network_scan': ('MODIFY_PHONE_STATE 기록 있음·추가 조건 미검증'
                         if grants.get('MODIFY_PHONE_STATE') is True
                         else 'MODIFY_PHONE_STATE 충족 미확인·통신사 권한 미검증'),
        'carrier_privileges': '미검증',
        'binder_call_verified': False,
        'gnss_hal_injection_verified': False,
        'cell_search_improvement_measured': False,
    }


def collect(adb, serial, runner=subprocess.run):
    records, properties, grants = [], {}, {}
    shell_uid = None
    for label, command in COMMANDS:
        result = base.run_command([adb, '-s', serial, *command], runner)
        ok = result['returncode'] == 0
        value = result['stdout'].strip() if ok else ''
        record = {'label': label, 'command': command,
                  'returncode': result['returncode'], 'status': result['status']}
        if label == '연결 상태':
            ok = ok and value == 'device'
            record['connected'] = ok
        elif command[:2] == ['shell', 'getprop']:
            # 이 속성 목록은 모델·OS 정보만 포함하며 기기 식별자를 요청하지 않는다.
            properties[label] = value if value else None
        elif label in ('shell 권한', 'V3 권한'):
            package = 'com.android.shell' if label == 'shell 권한' else PACKAGE
            found = bool(re.search(r'Package \[' + re.escape(package) + r'\]', value))
            record['package_record_found'] = found
            grants[label] = base.permission_observations(value if found else '')
        elif label == 'shell UID':
            shell_uid = int(value) if re.fullmatch(r'[0-9]{1,6}', value) else None
        else:
            # 도움말 문자열 존재는 실제 함수 호출 성공을 뜻하지 않는다.
            record['help_returned'] = bool(value)
        records.append(record)
        if label == '연결 상태' and not ok:
            break
    unknown = base.permission_observations('')
    shell = grants.get('shell 권한', unknown)
    app = grants.get('V3 권한', unknown)
    return {
        'schema': 1, 'captured_utc': datetime.now(timezone.utc).isoformat(),
        'kind': 'V3 읽기 전용 제어 경로 사전 확인', 'records': records,
        'properties': properties, 'shell_uid': shell_uid,
        'observed_shell_grants': shell, 'observed_v3_grants': app,
        'permission_scope': '패키지 덤프 기록 요약·사용자별 최종 권한 미검증',
        'shell_paths': path_assessment(shell), 'v3_paths': path_assessment(app),
        'limits': ['shell 권한은 V3 앱에 이전되지 않음',
                   'Shizuku·root·통신사 권한·삼성 Binder/HAL 경로 미검증',
                   '캐시 갱신은 GNSS HAL 위치 주입 또는 모뎀 탐색 개선의 증거가 아님'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--serial', help='ADB 대상 식별자·출력에 저장하지 않음')
    parser.add_argument('--out', type=Path, default=Path('captures/v3/control-capabilities.json'))
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args(argv)
    if args.plan:
        print(json.dumps(COMMANDS, ensure_ascii=False, indent=2))
        return 0
    if not args.serial:
        parser.error('--serial로 대상 기기를 지정하세요.')
    if args.out.exists():
        parser.error('기존 결과는 덮어쓰지 않습니다. 새 --out 경로를 지정하세요.')
    report = collect(args.adb, args.serial)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # 동시 실행에서도 기존 결과를 덮어쓰지 않는다.
    with args.out.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write('\n')
    complete = (len(report['records']) == len(COMMANDS)
                and all(r['returncode'] == 0 for r in report['records'])
                and report['records'][0]['connected'])
    print('읽기 전용 진단 저장 완료. 실제 제어 호출·성능 측정은 미실행.')
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
