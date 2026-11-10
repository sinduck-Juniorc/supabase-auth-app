# ver.3(포트 통신) — 새 대화 재개 지점

2026-11-10 사용자 요청에 따라 기존 대화의 사전 점검을 여기서 종료하고, 새 Codex 대화에서 포트 통신 단계로 이어간다. 이는 작업 단계·대화의 분기다. Git 작업 브랜치는 기존 승인된 `development/v3`를 유지한다. V2 태그·baseline/v2·앱 0.2.1은 변경하지 않는다.

## 이어받을 사실

- 사용자 PC와 단말은 USB로 연결돼 있고, 사용자 제공 ADB 결과는 재부팅 후 device다. 클라우드가 PC 또는 휴대폰을 직접 제어하는 환경은 아니다.
- 모델 SM-S947N, Android 17, SDK 37, One UI 속성 90000. shell UID 2000이며 NETWORK_SCAN, MODIFY_PHONE_STATE, LOCATION_HARDWARE, ACCESS_FINE_LOCATION의 granted=true 기록 확인. shell 통신사 권한 질의는 false. V3 패키지 경로 조회는 출력 없음.
- 사용자가 개발자 옵션의 3GPP AT 명령을 켜고 재부팅했다고 보고했다. 삼성 USB 모뎀은 정상 인식, 포트 COM3, Windows 서비스 modem. sys.usb.config는 mtp,adb. 설정 변경 전후 포트 비교가 없어 AT 옵션이 COM3를 생성했다고 단정하지 않는다.
- 장치 속성: VID_04E8, PID_6860, MI_01 및 Class_02/SubClass_02/Prot_01. CDC ACM/AT 프로토콜 계열을 나타내는 식별 정보지만 실제 AT 응답 증거는 아니다.
- 드라이버 INF 이름은 사용자 PC에서 oem140.inf, 적용 구역은 ssud.Install. OEM 번호와 COM 번호는 PC별·연결별로 달라질 수 있다.
- 첨부 INF를 분석했다. DriverVer=04/08/2026,2.21.4.0. 해당 VID/PID 모뎀 항목이 ssud.Install에 연결되며 ssud.Install.nt는 GenericAddReg 등을 참조한다. ssudmdm.sys 서비스와 하위 필터 정의가 있다. Windows의 modem 서비스 표시와 하위 필터 ssudmdm은 구분한다.
- GenericAddReg에는 기본 AT 및 CR 종료, OK/ERROR 응답 정의가 있다. 초기화 ATE0V1&D2&C1S0=0, 리셋 AT&F, 응답·전화 제어 항목도 있다. 이들은 드라이버 정의이며 S26+의 실제 허용 명령 목록이 아니다. 위치 입력·기지국 탐색 개선 명령은 이 INF에서 확인하지 못했다.

## CLAC 실측 체크포인트 — 2026-11-10

사용자 제공 Windows 실행 요약: COM3에서 `AT+CLAC`+CR 8바이트 전송, 2212바이트 수신, terminal_response=OK, status=ok, opened/write_attempted/closed=true, 두 오류 필드 null. c6b559a의 도구를 사용했다. command_names에 CSQ, CESQ, CREG/CGREG/CEREG/C5GREG 및 비표준 NCELL/SCELL/RSRP/RSRQ 등의 이름이 포함됐다. 명령 이름 노출은 각 실행형·읽기형·설정형의 허용·권한을 입증하지 않는다.

unparsed_lines=3, list_complete=false. 이는 엄격한 파서가 세 줄을 이름으로 저장하지 않았다는 뜻이며 OK 응답 실패를 뜻하지 않는다. 원문을 수집하지 않았으므로 세 줄의 내용·원인은 추정하지 않는다. 전체 목록 복원을 위해 재전송하지 않는다. 전체 결과 파일·개인 경로는 PC에 보존하며 공개 저장소에 올리지 않는다.

후속 후보는 표준 27.007 8.69절의 AT+CESQ 실행형(신호 품질 반환)이다. 전용 도구 준비 후 계획 확인부터 진행하며 아직 실제 CESQ는 미실행이다. NCELL/SCELL 등 제조사별 명령은 이름만으로 문법·효과를 추측하지 않는다. C5GNSSAI 계열은 5GS의 NSSAI/네트워크 슬라이스 관련 표기이므로 위성 GNSS 위치 주입 기능으로 해석하지 않는다. 위치 주입·셀 탐색 개선은 미검증이다.

## 최신 실측 체크포인트 — 2026-11-10

사용자 Windows CMD에서 c0fc902의 도구를 실행한 결과 요약을 받았다. COM3, 115200/8N1, 흐름 제어 없음, DTR/RTS False 요청 조건에서 `status=ok`, `opened=true`, `write_attempted=true`, `bytes_written=3`, `bytes_received=8`, `terminal_response=OK`, `closed=true`, 두 오류 필드 null을 확인했다. 이는 사용자 제공 실측 요약이며 클라우드 독립 측정은 아니다. 수신 원문은 수집하지 않아 8바이트 전체의 구성은 추정하지 않는다.

PC에 Python 설치 후 `py -3`으로 계획을 정상 출력했고, `py -3 zetamesh_at_probe.py --send-at --port COM3` 실행 결과를 공유받았다. 개인 결과 파일은 PC의 captures/v3에 보관하며 저장소에 올리지 않는다. 실행 절차는 [기본 AT 확인 절차](AT_RESPONSE_CHECK_ko.md)에 보존한다.

기본 AT 응답과 정상 close까지 확인했다. 다른 AT 명령 지원, 위치 주입, 기지국 탐색 개선, 장기 안정성은 입증하지 않았다. 아래 이전 대화 기록은 과거 상태다.

## 이전 대화의 정확한 중단 지점

COM3 열기, AT 전송, 응답 수신은 아직 실행하지 않았다. 다음 후보는 기본 AT 한 번의 응답 확인이지만 실행 방법·포트 설정·시간 제한·종료 처리는 아직 구현하지 않았다. 통신 성공, Binder/HAL 위치 주입, 실제 기지국 탐색 개선, V3 APK 설치·배포는 모두 미검증이다.

## 후속 준비 체크포인트

사용자 재연결 후 Windows 모뎀 조회에서 COM3/OK를 확인했다. 공식 TS 27.007 8.37절을 근거로 CLAC 목록 조회 전용 도구와 [절차](CLAC_CHECK_ko.md)를 준비했다. 이 준비 단계 이후 실제 CLAC 응답을 확인했으며 위 최신 체크포인트를 따른다. 기본 AT/CLAC 성공 시험을 반복하지 않는다. 이전의 도구 고정 AT만 지원한다는 기술은 기본 at_probe.py에 해당하며 새 clac_probe.py는 CLAC 한 번만 지원한다.

## 다음 작업

1. AGENTS.md, project-state.json, 이 문서와 CHANGELOG 최신 항목을 읽고 `python tools/resume_check.py`를 실행한다.
2. 기본 AT 성공 시험과 기존 USB/INF/ADB 사전 점검을 반복하지 않는다.
3. 후속 읽기 전용 AT 질의의 공식 정의와 단말 적용 근거를 검토한다. 기본 OK만으로 임의의 명령 지원을 가정하지 않는다. 초기화·리셋·다이얼·설정 변경 명령은 자동 실행하지 않는다.
4. 후속 질의를 선택하면 명령·목적·출력의 개인정보 범위·시간 제한을 명시하고 Windows CMD에서 한 단계씩 진행한다. 현재 도구는 고정 AT만 지원하며 임의 명령으로 수정해 실행하지 않는다.
5. 관찰·미실행·다음 작업을 작은 단위로 기록·커밋·푸시한다. 위치 주입·셀 탐색 제어 가능성은 별도 검증한다.

연결 확인이 필요할 때 사용자의 기존 CMD 위치(platform-tools-latest-windows)에서는 다음을 쓴다. 포트 통신 명령은 아니다.

```cmd
platform-tools\adb.exe devices
```

## 보존

개인 시리얼·사용자 PC 경로·첨부 원문·서명키를 공개 저장소에 넣지 않는다. 이번 기록은 관찰과 분석의 요약만 포함한다. 개인 ZIP의 PC 다운로드는 실패했고 서명키 이전도 미확인이다. 현재 단말 설정은 3GPP AT 켜짐으로 사용자 보고됐으며 자동 원복했다고 기록하지 않는다.

## 새 대화에 붙여넣을 프롬프트

ZetaMesh ver.3(포트 통신)을 이어서 진행해주세요. 한국어로 답변하세요. 저장소는 https://github.com/sinduck-Juniorc/supabase-auth-app, 작업 브랜치는 development/v3입니다. AGENTS.md, project-state.json, docs/SESSION_RESUME_ko.md, versions/v3/PORT_COMMUNICATION_RESUME_ko.md, versions/v3/CHANGELOG_ko.md를 읽고 가능하면 python tools/resume_check.py를 실행하세요. 사용자 Windows PC의 COM3에서 기본 AT 1회 전송 후 OK 응답과 정상 close를 확인했습니다. 기본 AT를 반복하지 말고 후속 읽기 전용 질의의 공식 근거와 단말 지원 범위 검토부터 진행하세요. V2는 수정하지 말고 개인 원문·서명키는 공개하지 마세요. 작은 단위로 검증·기록·커밋·푸시하세요.
