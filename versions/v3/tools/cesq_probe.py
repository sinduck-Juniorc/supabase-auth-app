"""Windows COM 포트에서 고정 AT+CESQ\r 한 번으로 신호 품질을 조회하는 V3 도구."""
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
MAX_BYTES = 4096


# 표준 코드 범위. 알 수 없음 코드는 측정값으로 변환하지 않는다.
FIELDS = ('rxlev', 'ber', 'rscp', 'ecno', 'rsrq', 'rsrp',
          'ss_rsrq', 'ss_rsrp', 'ss_sinr')
MAX_CODES = (63, 7, 96, 49, 34, 97, 126, 126, 127)
UNKNOWN_CODES = (99, 99, 255, 255, 255, 255, 255, 255, 255)


def parse_codes(line):
    match = re.fullmatch(rb'\+CESQ:\s*([0-9]{1,3}(?:\s*,\s*[0-9]{1,3}){5}(?:\s*,\s*[0-9]{1,3}){0,3})', line)
    if not match:
        return None
    values = [int(value.strip()) for value in match[1].split(b',')]
    # 기본 6필드 또는 NR 포함 9필드만 수용. 중간 형식은 추정하지 않는다.
    if len(values) not in (6, 9):
        return None
    result = {}
    for name, value, maximum, unknown in zip(FIELDS, values, MAX_CODES, UNKNOWN_CODES):
        if value != unknown and value > maximum:
            return None
        result[name] = dict(code=value, known=value != unknown)
    return result


def collect(factory, port, clock=time.monotonic):
    report = dict(status='not_started', opened=False, write_attempted=False,
                  bytes_written=0, bytes_received=0, terminal_response=None,
                  closed=False, error_type=None, close_error_type=None,
                  signal_codes=None, signal_valid=False, cesq_lines=0,
                  malformed_cesq_lines=0, unparsed_lines=0)
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
        report['bytes_written'] = connection.write(b'AT+CESQ\r')
        if report['bytes_written'] != 8:
            report['status'] = 'partial_write'
            return report  # 부분 전송도 재시도하지 않는다.
        deadline = clock() + RESPONSE_SECONDS
        pending = bytearray()
        while clock() < deadline and report['bytes_received'] < MAX_BYTES:
            chunk = connection.read(1)
            report['bytes_received'] += len(chunk)
            if chunk not in (b'\r', b'\n'):
                pending.extend(chunk)
                continue
            line = bytes(pending).strip()
            pending.clear()
            if not line or line == b'AT+CESQ':
                continue
            if line in (b'OK', b'ERROR') or line.startswith(b'+CME ERROR:'):
                report['terminal_response'] = ('+CME ERROR' if line.startswith(
                    b'+CME ERROR:') else line.decode('ascii'))
                report['status'] = 'ok' if line == b'OK' else 'error_response'
                report['signal_valid'] = (line == b'OK' and report['cesq_lines'] == 1
                                          and report['signal_codes'] is not None)
                break
            if line.startswith(b'+CESQ:'):
                report['cesq_lines'] += 1
                codes = parse_codes(line)
                if codes is None:
                    report['malformed_cesq_lines'] += 1
                report['signal_codes'] = codes
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
    mode.add_argument('--send-cesq', action='store_true')
    parser.add_argument('--port', default='COM3')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    if not re.fullmatch(r'COM[1-9][0-9]*', args.port, re.IGNORECASE):
        parser.error('Windows COM 번호만 허용합니다. 예: COM3')
    plan = dict(port=args.port.upper(), settings=SETTINGS, dtr=False, rts=False,
                command_hex='41 54 2b 43 45 53 51 0d', command_count=1,
                response_seconds=RESPONSE_SECONDS, receive_limit=MAX_BYTES,
                warning='포트 열기/닫기 때 드라이버에 의한 제어선 변화 가능. 실물 미검증.')
    if not args.send_cesq:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if sys.platform != 'win32':
        parser.error('실행은 COM 장치가 연결된 Windows PC에서만 가능합니다.')
    try:
        import serial
    except ImportError:
        parser.error('동일 Python에 pyserial 필요: python -m pip install pyserial==3.5')
    output = args.out or Path('captures/v3/cesq-' + datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%S%fZ') + '.json')
    # 저장 경로 오류/기존 파일은 포트를 열기 전에 확인한다.
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        report = dict(schema=1, captured_utc=datetime.now(timezone.utc).isoformat(),
                      plan=plan, result=collect(serial.Serial, args.port.upper()),
                      hardware_scope='수신 신호 품질 코드 1회 조회; 위치 주입·셀 탐색 개선 미검증')
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(report['result'], ensure_ascii=False, indent=2))
    print('개인 로컬 결과:', output)
    return 0 if report['result']['status'] == 'ok' and report['result']['signal_valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
