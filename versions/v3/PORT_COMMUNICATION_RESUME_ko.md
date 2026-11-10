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

## 이번 재개에서 준비한 실행 절차

[기본 AT 확인 절차](AT_RESPONSE_CHECK_ko.md)와 `tools/at_probe.py`를 추가했다. 포트 설정·시간 제한·close 처리를 구현했고 신규 모의 시험 8개를 통과했다. 사용자 PC에서는 먼저 `python versions\v3\tools\at_probe.py --plan`으로 확인한다. 실제 포트 열기·AT 전송은 여전히 미실행이며 사용자 결과를 기다린다. 아래 첫 작업의 절차 설계 단계는 완료됐으므로 반복하지 않는다.

## 이전 대화의 정확한 중단 지점

COM3 열기, AT 전송, 응답 수신은 아직 실행하지 않았다. 다음 후보는 기본 AT 한 번의 응답 확인이지만 실행 방법·포트 설정·시간 제한·종료 처리는 아직 구현하지 않았다. 통신 성공, Binder/HAL 위치 주입, 실제 기지국 탐색 개선, V3 APK 설치·배포는 모두 미검증이다.

## 새 대화의 첫 작업

1. AGENTS.md, project-state.json, 이 문서, versions/v3/CHANGELOG_ko.md를 읽고 미커밋 변경을 확인한다. 가능하면 `python tools/resume_check.py`를 실행한다.
2. 이미 확인한 설정 목록·도움말·전체 드라이버를 반복 수집하지 않는다. 필요하면 DEVICE_PREFLIGHT_ko.md를 참고한다.
3. COM3의 기본 AT 응답 확인 절차를 설계한다. 포트의 baud/parity/stopbits/flow control, DTR/RTS, timeout과 close 처리를 명시한다. 포트 열기 자체도 제어선 변화가 있을 수 있으므로 무조건 무변경이라고 표현하지 않는다. INF 초기화·리셋·다이얼 명령을 자동 재생하지 않는다.
4. 사용자 PC에서 실행할 방법을 안내한다. 사용자는 Windows CMD를 사용하며 여러 줄 붙여넣기 때 명령이 섞인 경험이 있다. 한 줄 명령 또는 검토 가능한 스크립트를 우선한다. ADB는 PATH에 없고 다운로드한 platform-tools 폴더에 있다.
5. 응답·오류·미실행·다음 명령을 작은 단위로 기록하고 커밋·푸시한다. 기본 AT 응답이 와도 위치 주입·셀 탐색 제어 가능성은 별도 검증한다.

연결 확인이 필요할 때 사용자의 기존 CMD 위치(platform-tools-latest-windows)에서는 다음을 쓴다. 포트 통신 명령은 아니다.

```cmd
platform-tools\adb.exe devices
```

## 보존

개인 시리얼·사용자 PC 경로·첨부 원문·서명키를 공개 저장소에 넣지 않는다. 이번 기록은 관찰과 분석의 요약만 포함한다. 개인 ZIP의 PC 다운로드는 실패했고 서명키 이전도 미확인이다. 현재 단말 설정은 3GPP AT 켜짐으로 사용자 보고됐으며 자동 원복했다고 기록하지 않는다.

## 새 대화에 붙여넣을 프롬프트

ZetaMesh ver.3(포트 통신)을 이어서 진행해주세요. 한국어로 답변하세요. 저장소는 https://github.com/sinduck-Juniorc/supabase-auth-app, 작업 브랜치는 development/v3입니다. AGENTS.md, project-state.json, docs/SESSION_RESUME_ko.md, versions/v3/PORT_COMMUNICATION_RESUME_ko.md, versions/v3/CHANGELOG_ko.md를 읽고 가능하면 python tools/resume_check.py를 실행하세요. 기존 대화는 COM3와 드라이버의 AT 정의 확인에서 종료됐고, 실제 포트 열기·AT 전송은 미실행입니다. 기본 AT 응답 확인 절차부터 설계하고 사용자 Windows PC에서 한 단계씩 진행하세요. V2는 수정하지 말고 개인 원문·서명키는 공개하지 마세요. 작은 단위로 검증·기록·커밋·푸시하세요.
