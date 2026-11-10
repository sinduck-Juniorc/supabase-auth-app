# 지원 명령 목록 조회 준비

## 근거와 범위

ETSI TS 127 007 V17.5.0(3GPP TS 27.007), 8.37절, 인쇄 148쪽은 `AT+CLAC` 실행형을 사용자에게 제공되는 AT 명령 목록 조회로 정의한다. 구현은 선택 사항이다. 이 정의는 SM-S947N의 실제 지원·전체 명령 노출·각 명령 실행 권한을 보장하지 않는다.

공식 원문: https://www.etsi.org/deliver/etsi_ts/127000_127099/127007/17.05.00_60/ts_127007v170500p.pdf

2026-11-10 사용자 재연결 결과: SAMSUNG Mobile USB Modem / COM3 / OK. 이는 Windows 등록 상태이며 포트를 열거나 새 AT를 전송한 결과는 아니다. 기존 기본 AT 성공은 반복하지 않는다.

## 도구와 실행

`tools/clac_probe.py`는 별도 다운로드 가능한 단일 파일이다. 기본 AT 도구는 수정하지 않았다. 명령은 `AT+CLAC` + CR 8바이트 한 번뿐이다. 기존 115200/8N1, 흐름 제어 없음, DTR/RTS False 요청을 유지한다. 쓰기 1초, 수신 관찰 10초(읽기당 0.1초), 최대 65536바이트, finally close. OS open/close 시간과 제어선 실제 변화는 드라이버에 의존한다. 자동 재시도·초기화·설정 변경은 없다.

저장소 루트 Windows CMD에서 한 줄씩 진행:

```cmd
py -3 versions\v3\tools\clac_probe.py --plan
```

계획 확인 후 실제 전송:

```cmd
py -3 versions\v3\tools\clac_probe.py --send-clac --port COM3
```

단독 다운로드한 파일 이름이 zetamesh_clac_probe.py라면 위 경로를 그 파일 이름으로 바꾼다. Python·pyserial은 이전 기본 AT 시험에서 사용한 환경을 재사용하며 재설치를 요구하지 않는다.

## 결과 해석과 보존

CR/LF로 끝나는 OK, ERROR, +CME ERROR를 판정한다. 표준의 AT 접두사가 있는 인자 없는 명령 이름만 엄격히 추출해 중복 제거한다. 에코 AT+CLAC는 제외하므로 이 항목의 목록 포함 여부는 판단하지 않는다. 인자·임의 문자열·예상 밖 URC는 저장하지 않고 unparsed_lines 수만 센다. 수신 원문은 저장하지 않는다. 표준과 다른 쉼표 목록·접두사 생략·인자 포함 표기는 추출하지 않으므로 원문 재요청이나 무조건 재전송 대신 파서 한계를 기록한다.

`status=ok`는 OK 종결 응답 관찰이다. 이름이 없으면 목록 확인 성공으로 보지 않는다. `list_complete=true`도 시간/용량 제한 없이 파서가 이해한 줄과 OK를 받았다는 뜻이며 제조사의 전체 지원 목록이나 권한 검증을 의미하지 않는다. ERROR/+CME ERROR/timeout/receive_limit이면 자동 재시도하지 않는다. closed=false 또는 close_error도 결과 검토 후 중지한다.

결과는 개인 PC captures/v3/clac-시간.json에 새 파일로 저장한다. 목록·오류 요약만 공유하고 개인 원문 파일은 공개 저장소에 올리지 않는다. 초기에는 출력된 요약을 검토하며 나열된 명령을 자동 실행하지 않는다. 위치 주입·셀 탐색 개선은 계속 미검증이다.
