# V3 개발 이력

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
