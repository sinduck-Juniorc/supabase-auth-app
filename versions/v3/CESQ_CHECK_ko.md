# CESQ 신호 품질 1회 조회

## CESQ 진단 재조회 결과 — 반복 중지

사용자 제공 00c7fe3 실행 요약: 송신 8/수신 44바이트, OK/정상 close/오류 없음. signal_codes=null, signal_valid=false, CESQ 줄 0, 미해석 줄 1. 마스킹 진단은 length=35, cesq_marker_present=false, truncated=false. 원문 문자열을 수집하지 않았으므로 오류 문구·지원 거부·원인을 단정할 수 없다. 신호 품질 응답을 확보하지 못한 것으로 기록하고 CESQ 재조회는 여기서 중지한다.

후속은 CLAC에 있던 기본 표준 AT+CSQ 1회 조회다. 별도 도구와 CSQ_CHECK_ko.md를 준비했으며 실제 CSQ는 아직 미실행이다. CESQ 종결 OK만으로 신호 측정 성공이나 NR 신호 수집 가능성을 주장하지 않는다.

## CESQ 첫 실측 — 형식 미해석

사용자 제공 d0e6d24 실행 요약: COM3, 송신 8바이트/수신 46바이트, status=ok, terminal_response=OK, 정상 close, 두 오류 필드 null. signal_codes=null, signal_valid=false, cesq_lines=0, malformed_cesq_lines=0, unparsed_lines=1. OK 종결 응답은 확인했지만 신호 품질 데이터는 확인하지 못했다. 원문 미저장으로 미해석 줄의 내용·원인은 복구/추정할 수 없다. 빈/가짜 응답·단말 오류·특정 구분자 차이로 단정하지 않는다.

진단 보완: 인식 접두사의 대소문자·콜론 앞 공백을 허용한다. 이는 모의 호환 시험이며 실제 원인 확인은 아니다. 미해석 줄은 영문자 X, 숫자 #, 공백 _ 등으로 가려 최대 8줄/줄당 128문자 형식만 기록한다. 실제 단어·숫자·개인 원문은 저장하지 않는다. CESQ 마커 존재 여부와 줄 길이도 저장한다. 형식이 여전히 다르면 신호 유효 판정 없이 이 진단만 검토한다. 동일 조건의 진단 재조회 한 번으로 원인 범위를 좁힐 수 있도록 준비했으며 보완본 실측은 아직 미실행이다.

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

신규 CESQ 11개, 기존 24개 모의 시험 통과. 첫 CESQ 실행은 위 기록과 같으며 진단 보완본 실측은 미실행이다.
