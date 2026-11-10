# CESQ 신호 품질 1회 조회

## 근거

공식 ETSI TS 127 007 V17.5.0(3GPP TS 27.007) 8.69절은 `AT+CESQ` 실행형을 수신 신호 품질 반환으로 정의한다. 사용자 CLAC 응답에도 CESQ 이름이 포함됐다. 실제 응답·형식·단말 구현은 아직 미확인이다.

https://www.etsi.org/deliver/etsi_ts/127000_127099/127007/17.05.00_60/ts_127007v170500p.pdf

## 실행 범위

별도 단일 파일 tools/cesq_probe.py를 제공한다. 기존 AT/CLAC 도구는 보존한다. 115200/8N1, 흐름 제어 없음, open 전 DTR/RTS False 요청, `AT+CESQ`+CR 8바이트 한 번, 쓰기 1초, 관찰 10초, 읽기당 0.1초, 최대 4096바이트, finally close. 제어선 실제 동작과 OS open/close 시간은 드라이버에 의존한다. 초기화·설정·망 탐색·재시도는 자동 실행하지 않는다.

Windows CMD, 같은 Python/pyserial 환경에서 한 줄씩:

```cmd
py -3 versions\v3\tools\cesq_probe.py --plan
```

계획 확인 후 한 번 전송:

```cmd
py -3 versions\v3\tools\cesq_probe.py --send-cesq --port COM3
```

단독 다운로드 시 경로 대신 zetamesh_cesq_probe.py를 쓴다. 포트 번호가 달라졌다면 Windows 모뎀 조회 결과를 사용한다.

## 해석과 개인정보

+CESQ 줄은 기본 6필드 또는 NR 포함 9필드를 수용한다. 필드 이름은 rxlev, ber, rscp, ecno, rsrq, rsrp, 추가 3필드는 ss_rsrq, ss_rsrp, ss_sinr다. 6필드 응답에는 NR 값을 만들어 넣지 않는다. 7/8필드·잘못된 코드 범위·문자열은 추정하지 않고 거부한다.

각 필드의 code는 코드값이며 dBm/dB 실측 수치와 같지 않다. 범위 양끝은 개방 구간이어서 단일 수치로 변환하지 않는다. rxlev/ber의 99와 나머지의 255는 known=false로 보존하며 신호 0 또는 서비스 불가로 단정하지 않는다. 표준상 해당 무선 방식이 아닐 때도 알 수 없음 값을 반환할 수 있다. 모든 코드가 알 수 없음이어도 응답 형식 자체는 유효할 수 있다.

status=ok는 OK 종결 관찰이다. signal_valid=true는 유효한 CESQ 한 줄과 OK를 받았다는 뜻이며, 코드가 모두 알려졌거나 측정이 최신임을 보장하지 않는다. 중복 CESQ는 모호하므로 false, 형식 오류는 malformed_cesq_lines로 기록한다. 다른 수신 줄은 원문 저장 없이 unparsed_lines 개수만 센다. close_error면 성공 종료로 처리하지 않는다. 오류/시간 초과 시 반복 실행하지 않고 결과부터 검토한다.

개인 결과는 captures/v3/cesq-시간.json에 새 파일로 생성한다. 공개 저장소에는 원문·개인 파일을 올리지 않는다. IMSI/IMEI/전화번호/셀 식별자·위치를 요청하지 않는다. 이 조회는 위치 주입·셀 탐색 가속의 검증이 아니다.

## 검증

python -m unittest discover -s versions/v3/tests -v

신규 CESQ 11개, 기존 24개 모의 시험 통과. 실제 Windows/휴대폰 CESQ 전송은 미실행이다.
