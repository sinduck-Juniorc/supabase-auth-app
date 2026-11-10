# 기본 CSQ 신호 조회

## 근거와 범위

ETSI TS 127 007 V17.5.0(3GPP TS 27.007) 8.5절의 실행형 AT+CSQ는 수신 신호 강도와 채널 오류율 코드를 반환한다. CLAC 목록에도 이름이 확인됐다. 목록 노출은 실제 호출 성공을 보장하지 않으며 단말 실측은 아직 없다. CESQ에서 유효한 신호 응답을 얻지 못한 뒤 별도로 준비한 기본 질의다.

공식 근거: https://www.etsi.org/deliver/etsi_ts/127000_127099/127007/17.05.00_60/ts_127007v170500p.pdf

## 실행

독립 실행 csq_probe.py. 기존 도구는 보존한다. 고정 AT+CSQ+CR 7바이트 한 번, 115200/8N1, 흐름 제어 없음, DTR/RTS False 요청, 쓰기 1초/수신 관찰 10초/4096바이트 제한/finally close. OS/드라이버에 의한 제어선 변화·open/close 호출 시간은 보장하지 않는다. 자동 재시도·초기화·설정 변경·망 스캔은 없다.

Windows CMD에서 먼저 계획만 확인:

```cmd
py -3 versions\v3\tools\csq_probe.py --plan
```

계획 확인 후 한 번 전송:

```cmd
py -3 versions\v3\tools\csq_probe.py --send-csq --port COM3
```

단독 다운로드 파일 이름이 zetamesh_csq_probe.py라면 위 경로를 그 이름으로 바꾼다. 기존 Python/pyserial 환경을 재사용한다.

## 해석·보존

+CSQ: rssi,ber의 숫자 두 필드만 저장한다. rssi 코드 0..31 또는 99, ber 0..7 또는 99를 수용한다. 99는 known=false이며 0으로 변환하지 않는다. 신호값 변환·세대 추정은 결과 검토 후 진행한다. LTE/NR RSRP 전용 측정 또는 5G 상세 정보와 동일하게 해석하지 않는다.

status=ok는 OK 종결, signal_valid=true는 유효한 CSQ 한 줄과 OK 관찰이다. 두 필드가 모두 99이면 형식은 유효해도 알려진 측정값이 없는 상태다. 중복/범위 오류/데이터 없는 OK는 signal_valid=false다. 혼합 대소문자 +CME Error도 오류로 판정한다. CESQ의 과거 가려진 문자열이 실제 이 오류였다고 단정하는 것은 아니다.

예상 밖 줄은 원문 없이 영문 X/숫자 #로 가린 형식·길이·CSQ 마커 여부를 최대 8줄/128문자로 기록한다. 결과는 PC captures/v3/csq-시간.json에 독점 생성하며 개인 파일은 공개하지 않는다. 임의 수신 문자열·개인 식별자·위치 요청은 저장/실행하지 않는다. 오류나 신호 미확인 시 같은 명령을 반복하지 않고 결과를 검토한다.

## 검증

신규 CSQ 모의 시험 8개 포함 총 46개 통과. CSQ 실제 단말 응답·위치 주입·셀 탐색 개선은 미검증이다.
