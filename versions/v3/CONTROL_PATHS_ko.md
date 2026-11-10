# V3 읽기 전용 제어 경로 확인

목표 단말은 한국형 Galaxy S26+, Android 17 / One UI 9다. 사용자 PC의 최신 모델·OS·권한·모뎀 관찰은 [실기기 사전 확인 요약](DEVICE_PREFLIGHT_ko.md)을 우선 읽는다. 아래는 도구의 설계와 일반 재개 절차다. 기존 보고서의 저장된 근거와 진단 함수를 재사용한다. 삼성 출하 펌웨어가 AOSP와 동일하다고 가정하지 않는다.

## 확인 범위

`tools/control_probe.py`는 ADB 연결 상태, 선택된 모델·OS 속성, shell UID, shell/V3 패키지 권한 기록, 전화·위치 명령 도움말만 조회한다. 설치·권한 부여·설정 변경·root 또는 Shizuku 시작·위치 주입·네트워크 스캔은 실행하지 않는다. ADB 서버는 클라이언트 실행 시 PC에서 시작될 수 있다. USB 디버깅 연결·승인은 사용자가 직접 준비한다.

원문 패키지 덤프·도움말·오류와 기기 선택 번호는 출력 파일에 저장하지 않는다. 모델·빌드와 권한 요약도 개인 단말 자료이므로 Git 제외 경로 `captures/v3/`에 둔다. 기존 결과는 덮어쓰지 않는다. 이 단계에는 APK나 서명키가 필요하지 않다.

## 호출 경로 판정

| 후보 | 읽기 전용으로 확인할 내용 | 아직 확인할 수 없는 내용 |
|---|---|---|
| V3 일반 앱 | `org.zetamesh.gnss.v3` 패키지의 실제 granted 기록 | 설치·런타임 승인·현재 사용자 AppOps·실제 API 성공 |
| ADB shell | UID와 `com.android.shell`의 granted 기록 | shell 권한을 V3에서 사용하거나 Binder 검사를 통과하는지 |
| 위치 서비스 `injectLocation` | LOCATION_HARDWARE + ACCESS_FINE_LOCATION 기록 | AOSP 근거의 도착점은 위치 캐시. GNSS HAL 주입·모뎀 제어와 구분 |
| `requestNetworkScan` | MODIFY_PHONE_STATE 기록 | 통신사 권한, 위치/AppOps, 구독, 인자, 서비스·HAL 지원·실제 등록 개선 |
| GNSS aiding / HAL | 기존 소스의 별도 경로만 참고 | 외부 위치를 받는 실제 삼성 진입점·권한·HAL 반영 |
| Shizuku·root·통신사/OEM | 이번 도구에서 실행하지 않음 | 현재 사용 가능 여부·UID 전환·허용된 API 경로 |

요청 목록은 부여 증거가 아니다. 누락·명령 실패·권한 기록 충돌은 `null`이다. 패키지 덤프는 사용자별 최종 권한 판정이 아니므로 두 권한이 true여도 ‘권한 기록 충족·호출 미검증’까지만 표시한다. 명령 종료 코드 0, 도움말 반환, NETWORK_SCAN 하나만으로 호출 가능을 판정하지 않는다. MODIFY_PHONE_STATE가 없더라도 통신사 권한 경로는 미검증으로 남긴다. shell 권한은 앱 권한에 합산하지 않는다.

근거: [기존 AOSP 발췌](../../reports/s26-cell-search/evidence/AOSP_EXCERPTS.md), [근거 목록](../../reports/s26-cell-search/SOURCES.md). 기존 관찰 앱의 보조정보 요청 반환값도 실제 주입 성공을 뜻하지 않는다.

## 다음 명령

저장소 루트에서 실행한다. 첫 두 명령은 단말 없이 가능하다.

```text
python tools/resume_check.py
python versions/v3/tools/control_probe.py --plan
```

사용자 PC에서 준비된 Platform Tools로 단말을 연결한 뒤 다음을 실행한다. `기기번호`는 실제 선택 값으로 바꾼다. Windows에서는 `python` 대신 `py -3.11`, `adb` 대신 `adb.exe`를 사용할 수 있다.

```text
adb devices
python versions/v3/tools/control_probe.py --adb adb --serial 기기번호 --out captures/v3/control-capabilities-01.json
```

오류 종료 코드 2면 요약의 `records`에서 실패한 명령을 먼저 확인한다. 종료 코드 0이어도 권한 누락은 미확인이다. 결과에서 제조사·모델·Android·SDK·One UI 속성이 목표 단말과 일치하는지 사람이 확인한다. 빈 속성만으로 OS 버전을 추정하지 않는다. 도움말 요약은 반환 여부만 나타내므로 구체적인 하위 명령은 이 단계에서 검증되지 않았다.

다음 개발은 개인 결과의 필요한 요약만 검토한 뒤, 실행 UID·패키지·사용자·AppOps·서비스별 호출 조건을 좁히는 것이다. 실제 제어 API 실행과 효과 측정은 별도 작업이다. 최신 위치를 어디에 입력할 수 있는지 확인되기 전에는 탐색 개선을 구현했다고 기록하지 않는다.
