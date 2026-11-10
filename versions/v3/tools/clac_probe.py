"""Windows COM 포트에서 고정 AT+CLAC\r 한 번으로 지원 명령 목록을 조회하는 V3 도구."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

SETTINGS = dict(baudrate=115200, bytesize=8, parity='N', stopbits=1,
                timeout=0.1, write_timeout=1.0,
                xonxoff=False, rtscts=False, dsrdtr=False)
RESPONSE_SECONDS = 10.0
MAX_BYTES = 65536


def collect(factory, port, clock=time.monotonic):
    report = dict(status='not_started', opened=False, write_attempted=False,
                  bytes_written=0, bytes_received=0, terminal_response=None,
                  closed=False, error_type=None, close_error_type=None,
                  command_names=[], unparsed_lines=0, list_complete=False)
    connection = None
    try:
        # 생성자에서 열지 않는다. 제어선 요청값을 open 전에 설정한다.
        connection = factory(port=None, **SETTINGS)
        connection.dtr = False
        connection.rts = False
        connection.port = port
        connection.open()
        report['opened'] = True
        connection.reset_input_buffer()
        report['write_attempted'] = True
        report['bytes_written'] = connection.write(b'AT+CLAC\r')
        if report['bytes_written'] != 8:
            report['status'] = 'partial_write'
            return report  # 부분 전송도 재시도하지 않는다.
        deadline = clock() + RESPONSE_SECONDS
        pending = bytearray()
        names = set()
        while clock() < deadline and report['bytes_received'] < MAX_BYTES:
            chunk = connection.read(1)
            report['bytes_received'] += len(chunk)
            if chunk not in (b'\r', b'\n'):
                pending.extend(chunk)
                continue
            line = bytes(pending).strip()
            pending.clear()
            if not line or line == b'AT+CLAC':
                continue
            if line in (b'OK', b'ERROR') or line.startswith(b'+CME ERROR:'):
                report['terminal_response'] = ('+CME ERROR' if line.startswith(
                    b'+CME ERROR:') else line.decode('ascii'))
                report['status'] = 'ok' if line == b'OK' else 'error_response'
                report['list_complete'] = line == b'OK' and bool(names) and not report['unparsed_lines']
                break
            # 표준 AT 접두사의 인자 없는 명령 이름만 저장한다.
            # 인자·식별값·예상 밖 URC는 저장하지 않고 줄 수만 센다.
            if re.fullmatch(rb'AT[+*$^%&]?[A-Z][A-Z0-9_]{0,47}', line):
                names.add(line.decode('ascii'))
                report['command_names'] = sorted(names)
            else:
                report['unparsed_lines'] += 1
        else:
            report['status'] = ('receive_limit' if report['bytes_received'] >= MAX_BYTES
                                else 'timeout')
    except Exception as exc:
        # OS 오류의 개인 경로·원문 응답을 공개 요약에 포함하지 않는다.
        report['status'] = 'io_error'
        report['error_type'] = type(exc).__name__
    finally:
        if connection is not None:
            try:
                connection.close()
                report['closed'] = True
            except Exception as exc:
                report['close_error_type'] = type(exc).__name__
                report['status'] = 'close_error'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--send-clac', action='store_true')
    parser.add_argument('--port', default='COM3')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    if not re.fullmatch(r'COM[1-9][0-9]*', args.port, re.IGNORECASE):
        parser.error('Windows COM 번호만 허용합니다. 예: COM3')
    plan = dict(port=args.port.upper(), settings=SETTINGS, dtr=False, rts=False,
                command_hex='41 54 2b 43 4c 41 43 0d', command_count=1,
                response_seconds=RESPONSE_SECONDS, receive_limit=MAX_BYTES,
                warning='포트 열기/닫기 때 드라이버에 의한 제어선 변화 가능. 실물 미검증.')
    if not args.send_clac:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if sys.platform != 'win32':
        parser.error('실행은 COM 장치가 연결된 Windows PC에서만 가능합니다.')
    try:
        import serial
    except ImportError:
        parser.error('동일 Python에 pyserial 필요: python -m pip install pyserial==3.5')
    output = args.out or Path('captures/v3/clac-' + datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%S%fZ') + '.json')
    # 저장 경로 오류/기존 파일은 포트를 열기 전에 확인한다.
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        report = dict(schema=1, captured_utc=datetime.now(timezone.utc).isoformat(),
                      plan=plan, result=collect(serial.Serial, args.port.upper()),
                      hardware_scope='지원 명령 이름 조회; 목록 항목의 실행·권한은 미검증; 위치 주입·셀 탐색 개선 미검증')
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(report['result'], ensure_ascii=False, indent=2))
    print('개인 로컬 결과:', output)
    return 0 if report['result']['status'] == 'ok' else 2


if __name__ == '__main__':
    raise SystemExit(main())
