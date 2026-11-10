# V3 개발 이력

## 2026-11-10 · 오류 검토 및 이전 개발자 옵션 자료 재확인

- 조사: 삼성 공식 개발자/지원 도메인에서 SM-S947N의 포트 허용표를 확인하지 못함. 표준 9.1/9.2의 CME 숫자/문구 의미를 검토. 모델 미지원으로 단정하지 않음.
- 보완: csq_probe.py에서 CME 상세를 숫자 코드·엄격한 표준 문구 분류·제한된 단서로 보존. 임의 문구는 원문 저장하지 않음. 고정 CSQ 송신·설정·제한 유지, 추가 전송 미실행. 5개 신규 포함 51개 모의 시험 통과.
- 사용자 지적 반영: 이전 「삼성 개발자 옵션 스크린샷 정리」의 JSONL 생성/전사 기록과 저장소 요약 대조. 126항목 자료의 AT off는 촬영 당시이며 이후 on·재부팅 보고가 최신. 가상 모뎀/GNSS 측정/업링크/AI GRO를 CSQ 권한 옵션으로 해석하지 않음. 원본 파일 전체 재검증이라고 주장하지 않으며 개인 원문/경로 공개 없음.
- 문서: DEVICE_PREFLIGHT와 PORT_ERROR_REVIEW, 상태 갱신. JSON 파싱/재개/diff 검사. V2 변경 없음.
- 다음: 옵션 기록을 우선 검토하고 필요하면 현재 AT 설정을 화면에서 읽기만 확인. 최소 CME 진단의 실물 전송은 아직 미실행, 자동 설정 변경/재시도 없음.

## 2026-11-10 · CSQ 오류 응답 확인 및 신호 질의 중지

- 사용자 실측: 08cc4a6 CSQ 실행, COM3 송신 7/수신 38바이트, status=error_response, +CME ERROR, 정상 close, 입출력/close 예외 없음. 신호 값 없음, CSQ/잘못된 CSQ/미해석 줄 모두 0. 클라우드 독립 실측 아님.
- 한계: 오류 번호/문구는 도구가 저장하지 않아 원인 미확인. 수신 길이로 복원 불가. 미지원·권한·단말 상태를 단정하지 않고 CESQ 이전 응답도 같은 오류라고 소급 확정하지 않음. CLAC 목록 노출은 실행 성공·접근 권한을 보장하지 않음.
- 변경: 상태·CSQ 절차·포트/세션 재개·이력 문서 갱신. 개인 경로/원문/결과 파일 공개 없음. V2 코드/APK/기준점 변경 없음.
- 검증: JSON 파싱, resume_check, git diff --check. 문서 변경이므로 46개 코드 모의 시험·앱 빌드는 반복하지 않음. 신호 수집·위치 주입·셀 탐색 개선 미입증.
- 다음: CSQ/CESQ 재전송·다른 신호 명령 순차 시도 중지. 공식 삼성/단말 포트 허용 자료 조사와 필요 시 오류 코드/분류만 보존하는 최소 진단 설계 검토. CMEE·초기화·리셋·설정 변경은 실행하지 않음.

## 2026-11-10 · CESQ 진단 결과 및 기본 CSQ 준비

- 사용자 실측: 00c7fe3 CESQ 송신 8/수신 44바이트, OK/정상 close/오류 없음. 신호 값 없음, 미해석 1줄/35바이트/CESQ 마커 없음. 원문이 가려져 원인·문구를 단정할 수 없음. CESQ 반복 중지.
- 변경: 상태/재개/CESQ 기록 갱신, 독립 csq_probe.py·CSQ_CHECK_ko.md·시험 추가. 근거는 공식 TS 27.007 8.5절과 CLAC의 CSQ 이름. 고정 CSQ+CR 7바이트 1회, 기존 설정/제한/종료 처리 유지. 2필드 코드만 검증, 99 미확인 보존, 비정상 원문은 마스킹 형식만 저장. CME 오류의 혼합 대소문자도 처리하며 이것이 이전 CESQ 원인이었다고 주장하지 않음.
- 검증: 신규 8개 포함 46개 모의 시험 통과, 계획 출력/JSON/재개/diff 검사. CSQ 실측·위치 주입·셀 탐색 개선은 미실행/미검증. V2 코드/APK/기준점 변경 없음.
- 다음 명령: 사용자 PC py -3 zetamesh_csq_probe.py --plan 후 --send-csq --port COM3 한 번. CESQ/CLAC/기본 AT 반복 없음. 개인 원문 파일 공개 없음.

## 2026-11-10 · CESQ 첫 응답 기록 및 형식 진단 보완

- 사용자 실측: COM3, 송신 8/수신 46바이트, OK/정상 close/오류 없음. signal_codes=null, signal_valid=false, cesq_lines=0, malformed_cesq_lines=0, unparsed_lines=1. 신호 품질 값은 미확인. 원문을 저장하지 않아 원인·줄 내용은 추정하지 않음.
- 변경: CESQ 파서 대소문자/콜론 앞 공백 허용, 미해석 줄의 마스킹 형식·길이·CESQ 마커 여부만 최대 8줄/128문자로 기록. 단어·실제 숫자·원문은 저장하지 않음. 고정 송신 명령·시간 제한·제어선·설정은 유지.
- 검증: 신규 호환/원문 미보존/진단 상한 3개 포함 총 38개 모의 시험 통과. JSON/재개 검사/diff 검사. 보완본 실제 단말 응답은 미검증. 이 호환 보완이 실제 원인을 해결했다고 주장하지 않음.
- 다음: 보완본을 별도 진단 목적으로 한 번 실행하고 signal_codes/unparsed_shapes 검토. 기본 AT/CLAC 반복 및 다른 명령 자동 실행 없음. V2 코드/APK/기준점 변경 없음.

## 2026-11-10 · CESQ 신호 품질 조회 준비

- 완료: CLAC에 나열된 CESQ와 공식 TS 27.007 V17.5.0 8.69절을 근거로 cesq_probe.py, CESQ_CHECK_ko.md, 전용 시험 추가. 기본 AT/CLAC 도구 보존.
- 동작: 고정 AT+CESQ+CR 8바이트 한 번, 기존 포트 설정 유지. 쓰기 1초/관찰 10초/4096바이트 상한/finally close. 6/9필드 코드 범위 검증, 알 수 없음 코드 보존, 중복 CESQ 모호성 판정. 원문·개인 식별자 미저장. dBm/dB 단일값으로 임의 변환하지 않음.
- 검증: 신규 모의 시험 11개(6/9필드, 알 수 없음/0, 범위/필드 오류, 중복, 빈 OK/URC, ERROR/CME, 부분 응답, 입출력/close/부분 쓰기, 상한, 계획)와 기존 24개, 총 35개 통과. --plan, JSON 파싱, resume_check, git diff --check 통과.
- 미실행: 실제 Windows/단말 CESQ 응답, 위치 주입·셀 탐색 개선. V2 코드/APK/기준점 변경 없음.
- 다음 명령: 사용자 PC py -3 zetamesh_cesq_probe.py --plan. 계획 확인 후 --send-cesq --port COM3 한 번. 실패 시 재시도 없이 요약 검토. 개인 파일은 PC에 유지.

## 2026-11-10 · 사용자 PC CLAC 응답 확인

- 완료: c6b559a 도구의 사용자 실행 요약 수신. COM3, 8바이트 전송, 2212바이트 수신, status=ok/terminal_response=OK, 정상 close, 오류 없음. 표준 CSQ/CESQ/등록 상태 및 제조사별 명령 이름 노출 확인. 클라우드 독립 실측은 아님.
- 한계: unparsed_lines=3, list_complete=false. 세 줄 내용·원인은 원문 미수집으로 미확인. 응답 실패로 해석하지 않으며 전체 목록이라고 주장하지 않음. 명령 이름이 있다고 각 형식 실행·권한이 입증되는 것은 아님.
- 해석: C5GNSSAI 계열은 NSSAI/네트워크 슬라이스 계열이며 위성 GNSS 주입 근거가 아님. NCELL/SCELL/RSRP 등의 비표준 문법·효과는 이름으로 추정하지 않음. 공식 표준 근거 URL은 CLAC_CHECK에 보존.
- 변경: 상태·CLAC 절차·포트/세션 인수인계·이 이력 갱신. 원문 결과·전체 파일·개인 경로 공개 없음. V2 코드/APK/기준점 변경 없음.
- 검증: JSON 파싱, resume_check, git diff --check. 문서 변경이므로 모의 시험·앱 빌드 반복 없음. 실물 CESQ·위치 주입·셀 탐색 개선은 미실행/미검증.
- 다음: 기본 AT/CLAC 재실행 없이 표준 27.007 8.69절 AT+CESQ 신호 품질 조회 전용 도구 준비, 계획 확인부터 진행. 현재 단말에서 CESQ의 실제 응답 형식은 미확인.

## 2026-11-10 · 재연결 및 CLAC 조회 준비

- 사용자 관찰: USB 재연결 후 Windows 모뎀 조회에서 SAMSUNG Mobile USB Modem / COM3 / OK. 포트 열기·새 AT 전송은 이 조회에 포함되지 않음.
- 근거: ETSI TS 127 007 V17.5.0 8.37절의 AT+CLAC(사용자에게 제공되는 명령 목록 요청), 선택 구현. 삼성 단말 지원은 미확인. 공식 URL은 CLAC_CHECK_ko.md에 기록.
- 변경: 별도 clac_probe.py, 모의 시험, CLAC_CHECK_ko.md 추가 및 상태/재개 문서 갱신. 기본 AT 도구는 보존. 고정 CLAC+CR 8바이트 한 번, 10초/65536바이트 수신 제한, finally close, 원문 미저장, 엄격한 명령 이름 추출. 비표준 줄은 개수만 기록.
- 검증: 신규 8개 및 기존 16개, 총 24개 모의 시험 통과. 계획 출력·JSON 파싱·resume_check·git diff --check 확인. 실제 CLAC·Windows 드라이버·위치 주입·셀 탐색 개선 미검증. V2 코드/APK/기준점 변경 없음.
- 다음 명령: 사용자 PC의 단독 다운로드 파일에서 py -3 zetamesh_clac_probe.py --plan. 계획 확인 후 --send-clac --port COM3 한 번. ERROR/시간 초과 시 자동 재시도하지 않고 요약 검토. 나열된 명령 자동 실행 없음.

## 2026-11-10 · 사용자 PC 기본 AT 응답 확인

- 완료: c0fc902 도구를 사용자 Windows PC에서 실행한 결과 요약 수신. COM3, 115200/8N1, 흐름 제어 없음, DTR/RTS False 요청. status=ok, opened=true, write_attempted=true, bytes_written=3, bytes_received=8, terminal_response=OK, closed=true, error_type/close_error_type=null.
- 근거 범위: 사용자 제공 실측 요약이며 클라우드 독립 실측 아님. 수신 원문 미수집으로 8바이트의 전체 구성은 추정하지 않음. PC Python 설치 후 py -3 계획 출력과 실제 실행 결과 확인. 개인 경로·결과 파일·원문은 커밋하지 않음.
- 변경: project-state.json, SESSION_RESUME, PORT_COMMUNICATION_RESUME, AT_RESPONSE_CHECK와 이 CHANGELOG를 현재 상태로 갱신. 이전 체크포인트는 이력으로 보존.
- 검증: JSON 파싱, resume_check 브랜치·V2 기준점 검사, git diff --check. 문서만 변경하여 코드 시험·앱 빌드는 반복하지 않음.
- 미검증: 다른 AT 명령 지원, 위치 주입·셀 탐색 개선, 장기 안정성, V3 APK 배포. 기본 응답만으로 이 항목의 성공을 주장하지 않음.
- 다음: 기본 AT를 재실행하지 않고 후속 읽기 전용 AT 질의의 공식 정의·단말 지원 근거를 검토. 아직 추가 실물 전송 명령은 선정하지 않음. 재개 시 python tools/resume_check.py.
- V2 코드·APK·태그·baseline 브랜치 변경 없음. 개인 백업·서명키 이전 미확인 유지.

## 2026-11-10 · 기본 AT 1회 확인 도구 준비

- 완료: 60844f2에서 별도 V3 worktree로 재개. `tools/at_probe.py`, `tests/test_at_probe.py`, `AT_RESPONSE_CHECK_ko.md` 추가, 상태·재개 문서 갱신.
- 동작: 기본/--plan은 포트를 열지 않음. Windows --send-at에서 COM3 115200/8N1, 흐름 제어 없음, DTR/RTS False 요청, AT+CR 한 번만 전송. 쓰기 1초·응답 관찰 3초·4096바이트 상한, finally close. 초기화·리셋·다이얼·자동 재시도 없음.
- 보존: 원문 응답·개인 식별자·OS 오류 원문 미저장. 로컬 captures/v3에 새 요약 파일만 생성. 포트 열기/닫기 제어선 변화 가능성을 명시.
- 검증: resume_check 브랜치·V2 태그 기준점 통과, 원격 baseline/v2와 V2 태그 peeled commit 고정 해시 일치. 신규 모의 시험 8개(단일 송신, 오류 응답, 무응답/부분 응답, 입출력 실패, 부분 쓰기, close 실패, 수신 상한, 계획 모드)와 기존 8개 통과. --plan, JSON 파싱, git diff --check 통과.
- 미실행/제약: 클라우드는 사용자 PC COM3에 접근할 수 없음. Windows pyserial/드라이버 실측, 실제 AT 응답·위치 주입·셀 탐색 개선·APK 빌드/배포 미검증. Supabase/Vercel은 이번 작업에서 사용하지 않음.
- 다음 명령: 사용자 Windows에서 `python versions\v3\tools\at_probe.py --plan`. 이후 동일 Python에 pyserial==3.5 설치, 문서 조건 확인 후 `python versions\v3\tools\at_probe.py --send-at --port COM3` 한 번 실행. result 요약을 받아 판단하며 무응답 시 자동 재시도하지 않음.
- V2: 코드·APK·태그·baseline 브랜치 변경 없음. 실물 회귀 시험 미실행. 개인 백업·서명키 이전 미확인 유지.

## 2026-11-10 · 대화 분기: ver.3(포트 통신)

- 사용자 요청: 이 대화의 사전 점검을 종료하고 새 Codex 프롬프트에서 포트 통신 단계로 재개. Git 브랜치는 development/v3 유지.
- 완료: USB 식별자·CDC ACM/AT 계열 표기와 첨부 INF 분석 요약, 단계 경계·새 대화용 프롬프트·첫 작업을 PORT_COMMUNICATION_RESUME_ko.md에 기록. project-state.json과 세션 재개 문서 갱신.
- 검증: JSON 파싱, resume_check의 브랜치·V2 기준점 검사, git diff --check. 문서 작업이므로 앱 빌드·시험 반복은 생략.
- 미실행: COM3 열기·AT 전송·응답 수신·위치 주입·셀 탐색 개선 검증. 이번 대화에서 새 통신 시험을 시작하지 않음.
- 다음 명령: 새 대화에서 python tools/resume_check.py. 포트 통신 명령은 인수인계의 조건을 검토한 뒤 설계.
- 원문 INF·개인 정보·키 업로드 없음. V2 코드·APK·기준점 변경 없음. PC 백업·서명키 이전 미확인 유지.

## 2026-11-10 · 사용자 PC 사전 관찰 체크포인트

- 완료: 사용자 제공 결과로 모델/OS, UID 2000, shell의 네 권한 granted 기록, 통신사 권한 false, V3 설치 경로 미확인, 위치/전화 도움말을 요약. 사용자가 3GPP AT 설정을 켜고 재부팅한 뒤 ADB device 및 Windows 삼성 모뎀 COM3/service modem을 보고. USB 속성은 mtp,adb.
- 변경: `DEVICE_PREFLIGHT_ko.md`, 제어 경로/세션 재개 문서, project-state.json. 개인 원문·시리얼·설정 JSONL은 포함하지 않음. V2와 앱 코드는 변경하지 않음.
- 검증: 사용자 제공 관찰이며 클라우드 독립 실측 아님. 로컬 재개 검사와 문서 diff/JSON 검사 실행. 문서·상태 변경이므로 앱 빌드·기존 코드 시험 반복은 생략.
- 미실행: AT 포트 열기·질의, V3 설치, Binder/HAL 호출, 위치 주입, 셀 탐색/등록 성능 비교. 포트 존재만으로 제어 성공을 판정하지 않음. 설정 변경 전후 비교가 없어 AT 옵션과 포트 생성의 인과도 미확인.
- 다음: COM3의 지원 근거·연결 조건과 읽기 질의 범위를 먼저 검토. 기존 CMD에서 연결 재확인이 필요할 때만 `platform-tools\adb.exe devices`. 도움말/권한 전체 재수집과 추측 AT 명령 실행은 하지 않음.
- 보존: V2 회귀 시험 불필요(앱 변경 없음). 개인 ZIP PC 다운로드·서명키 이전 미확인 유지.

## 2026-11-10 · 읽기 전용 제어 경로 사전 점검

- 목적: 한국형 S26+ / Android 17 / One UI 9의 실제 권한 확인 준비. 기존 관찰을 가속 또는 위치 주입 성공으로 판정하지 않음.
- 완료: `versions/v3/tools/control_probe.py`, `tests/test_control_probe.py`, `CONTROL_PATHS_ko.md` 추가. 기존 S26 보고서의 진단 함수를 재사용하고 shell UID 및 V3 패키지 권한 조회를 보완. 기존 보고서·도구·앱·APK는 수정하지 않음.
- 출력: 원문 덤프·도움말·오류·기기 선택 번호를 저장하지 않고 모델/OS와 권한 요약만 보관. shell/V3 권한을 분리하고 요청 목록·누락·충돌을 미확인으로 처리. 기본 출력 `captures/v3/`는 Git 제외이며 기존 결과를 덮어쓰지 않음.
- 검증: `python tools/resume_check.py`의 브랜치·V2 기준점 검사 통과. 원격 `baseline/v2` 및 annotated tag의 peeled commit은 고정 해시 `1cf897fe85480fdd0773cc8286746a9e739aa405`와 일치. GitHub 연결 도구의 저장소 읽기·push 권한 조회 성공.
- 시험: 신규 unittest 8개, 기존 probe 시험 5개 통과. `--plan` 정상 출력. ADB가 없는 실제 클라우드 실행은 종료 코드 2·`실행 불가`로 기록되고 후속 shell 명령이 실행되지 않음. 실패 결과의 Git 제외 확인. `git diff --check` 통과.
- 미실행/원인: 현재 클라우드에 ADB와 연결된 단말이 없어 모델/OS/실제 권한·Binder·GNSS HAL·통신사 권한·성능은 미검증. APK 빌드·설치·위치 주입·망 스캔 미실행. Supabase/Vercel은 이번 Android 작업에서 미사용·접근 미검증. 개인 ZIP의 PC 다운로드·서명키 이전은 여전히 미확인.
- 다음 명령: 사용자 PC의 저장소 루트에서 `python versions/v3/tools/control_probe.py --plan`, `adb devices`, `python versions/v3/tools/control_probe.py --adb adb --serial 기기번호 --out captures/v3/control-capabilities-01.json`. Windows의 실행기 선택과 판정 기준은 `CONTROL_PATHS_ko.md` 참조.
- 다음 판단: 실기기 요약의 모델·빌드·shell/V3 권한을 분리 검토한 뒤 사용자/AppOps/서비스 호출 조건을 좁힘. 권한 기록 충족만으로 호출 성공·캐시→HAL·모뎀 반영을 주장하지 않음.
- V2 회귀: 이번 단위는 V3 도구·문서와 재개 상태만 변경. V2 코드/APK/태그/브랜치 변경 없음, V2 실물 회귀 시험 미실행.

## 2026-11-10 · 분리 준비

기준: zetamesh-v2.0.0, 앱 0.2.1. 아직 V3 기능 또는 V3 APK의 구현·실기기 검증을 완료한 것은 아니다.

- 개발 브랜치: development/v3
- 별도 앱 식별자: org.zetamesh.gnss.v3
- 이후 각 변경에는 목적 / 변경 파일 / 검증 / 실물 결과 / 알려진 제한 / V2 회귀 필요 여부를 기록한다.
- 새로운 제어 경로가 확인되기 전 관찰을 가속 구현이라고 표시하지 않는다.

개발 준비 변경: manifest를 별도 package·앱 이름·완전한 Activity 클래스 이름으로 설정했다. 화면·로그 버전은 0.3.0-dev, 빌드 출력은 ZetaMesh-V3-dev.apk다. 과거 downloads의 APK들은 V2 이력이며 V3로 배포하지 않는다. 이번 단계에서는 V3 APK를 빌드·배포하지 않았다.

## 2026-11-10 · 무료 플랜의 작업 재개 구조

- 개발 지침, project-state.json, SESSION_RESUME 문서와 로컬 재개 검사 추가.
- Supabase 웹 인증의 기존 getUser·쿠키 갱신 경로를 검토했으며 앱 인증 코드는 변경하지 않음.
- 로컬 V3 브랜치와 V2 고정 태그 일치를 확인. 외부 OAuth·배포 가용성과 장기 세션 유지는 미검증.
- 다음 작업: 서비스 연결 유형 확인 후 필요한 연결만 읽기 전용 진단. 기능 목표는 project-state.json 참조.
- V2 회귀: 불필요, V2 코드·APK 변경 없음.

### 사용량 한도 의미 정정

사용자가 ‘세션 중단’을 AI 사용량 초과로 명확히 했다. 상태 문서·개발 지침에 작은 단위 저장, 한도 경고 시 저장 우선, 재개 절차를 추가했다. OAuth 정책은 부수적 복구 항목으로 남긴다. 한도 우회·자동 모델 전환·중단 시점 저장 보장은 구현하지 않는다. 앱 코드 변경 없음.
