# 갤럭시 Z Fold3 내장 GNSS 탐색 가속: 우회 경로 조사 및 코드 적용 보고서

작성일: 2026-11-09. 대상 가정: Galaxy Z Fold3, 공식 Android 15 / One UI 7.0. 실제 사용자 단말의 모델 접미사·통신사·빌드 번호는 아직 확인하지 않았다. GPS 모듈은 미구매다.

## 1. 결론

일반 앱에서도 내장 GNSS의 시간 보조정보와 PSDS 보조데이터 갱신을 요청하는 경로가 있다. 이 경로를 실행하고 실제 GNSS 첫 측정 콜백을 기록하는 Android APK를 구현·빌드·서명 검증했다. GPS 모듈 없이 Fold3만으로 첫 시험을 할 수 있다.

그러나 요청을 보냈다는 사실은 삼성 펌웨어의 데이터 다운로드·칩 주입·TTFF 단축이 성공했다는 증거가 아니다. 실제 Fold3에는 설치하지 못했고, 개선 시간이나 성공률을 측정하지 않았다.

**현재 APK는 휴대폰 운영체제의 보조정보 갱신 경로를 시험한다. R4에서 BLE로 받은 좌표를 Fold3 내장 GNSS에 넣는 기능은 구현하지 못했다. 따라서 원래의 BLE 기반 GNSS 가속 MVP가 동작했다고 주장하지 않는다.**

## 2. 단말 가정의 근거

삼성의 SM-F926N 공식 업데이트 이력은 Android 15와 One UI 7.0을 명시한다. 조사 시 페이지 상단 빌드는 F926NKSSEKZH5, 배포일 2026-08-31이었다. 이는 조사한 모델의 이력이며 사용자 단말이 같은 빌드라는 뜻은 아니다. 앱은 SDK 35(Android 15)를 대상으로 빌드했고 Android 11(API 30) 이상 설치를 허용한다. 실행 로그에 실제 모델·Android 버전·빌드 fingerprint를 기록한다. One UI 버전은 사용자 설정 화면에서 확인해야 한다.

공식 근거: https://doc.samsungmobile.com/SM-F926N/019559210813/kor.html

## 3. 조사한 경로와 적용 판단

| 경로 | 내장 GNSS에 미칠 수 있는 영향 | 권한·제약 | 이번 적용 |
|---|---|---|---|
| 시간 보조정보 갱신 요청 | 시스템이 GNSS 시간 보조정보 갱신을 수행할 수 있음 | 제조사 구현·시간 소스·연결 상태에 의존 | APK B/C 모드 |
| PSDS 갱신 요청 | 지원하는 HAL에서 예측 위성 보조데이터를 다운로드·주입할 수 있음 | HAL 지원·제조사 서버 설정·인터넷 필요 | APK B/C 모드 |
| 실제 네트워크 위치 요청 | 시스템이 얻은 거친 위치가 GNSS 보조 경로에 활용될 가능성 | OEM 구현에 의존, 외부 BLE 좌표 주입 아님 | APK C 모드, B와 별도 비교 |
| GNSS 미리 켜기 | 사용자가 필요할 때 이미 warm 상태일 수 있음 | 대기 시간·전력 비용을 앞당긴 것일 수 있음 | 가속 실증으로 채택하지 않음 |
| BLE 위치를 앱 지도에 사용 | 앱의 표시를 빠르게 할 수 있음 | 내장 GNSS TTFF 개선을 뜻하지 않음 | 사용자 필수 조건을 만족하지 않음 |
| 모의 위치 제공자 | 앱에 시험 좌표를 공급 | 실제 위성 측정 가속이 아님; AOSP의 관련 주입 경로는 mock 좌표를 배제 | 제외, 시험 로그에서도 거부 |
| ADB/Shizuku | shell에 실제 부여된 권한 범위의 시스템 호출 | root/플랫폼 서명 권한을 자동으로 얻지 못함 | 범용 우회로 판단하지 않음 |
| 플랫폼 서명 시스템 앱·OEM GNSS HAL 연동 | 적절한 권한과 HAL 인터페이스가 있으면 직접 aiding 가능성 | 삼성/OEM 협력, 시스템 통합과 실기기 검증 필요 | 미래의 정식 제품 경로 |
| 부트로더 해제·root·커스텀 프레임워크 | 시스템 권한·주입 경로를 수정하는 실험 가능성 | 모델별 잠금, 데이터 초기화 가능성, Knox 영구 영향, HAL/SELinux 제약 | 조사만 수행, 단말 변경 미실행 |

권한을 획득했다고 모든 HAL 기능이 동작하는 것은 아니다. 숨겨진 API를 reflection으로 호출하거나 SDK 수준을 낮추는 것만으로 서버 측 권한 검사가 사라지지 않는다. `pm grant LOCATION_HARDWARE`가 일반 앱에 통한다고 가정하지 않는다. Shizuku의 ADB 모드도 shell 권한 한계 안에서 작동한다.

## 4. 소스에서 확인한 사실

- 공개 `LocationManager.sendExtraCommand()`로 공급자별 추가 명령을 전달할 수 있다. `ACCESS_LOCATION_EXTRA_COMMANDS`는 AOSP manifest에서 normal 권한이다. 앱은 정확한 위치 권한도 요청한다.
- AOSP GNSS 공급자는 `force_time_injection`과 `force_psds_injection`을 처리한다. PSDS 경로는 지원 여부를 먼저 확인한다. Google GNSSLogger도 보조정보 요청 기능을 구현한 공개 사례다.
- 현행 AOSP `sendExtraCommand()`는 호출 후 항상 true를 반환한다. 따라서 앱은 이를 `api_return`으로 기록하고 `injection_confirmed=false`를 함께 기록한다. true를 “지원됨”이나 “주입 성공”으로 해석하지 않는다.
- AOSP `LocationManager.injectLocation()`은 숨겨진 시스템 API이며 LOCATION_HARDWARE와 ACCESS_FINE_LOCATION을 요구한다. 그 주석은 마지막 알려진 위치 제공도 설명하므로, 이 메서드 호출 자체를 GNSS 칩 가속과 동일시해서도 안 된다. 직접 칩 aiding을 주장하려면 실제 provider→HAL 경로를 추가 확인해야 한다.
- 실제 네트워크 공급자의 위치를 사용하는 시스템 내부 경로와 임의 BLE 좌표를 그 경로에 넣는 행위는 다르다. C 모드는 실제 NETWORK_PROVIDER를 요청할 뿐 좌표를 바꿔 넣지 않는다.

근거 링크:

1. 공개 API: https://developer.android.com/reference/android/location/LocationManager#sendExtraCommand(java.lang.String,%20java.lang.String,%20android.os.Bundle)
2. Android 권한 정의: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/AndroidManifest.xml
3. LocationManager 구현: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/location/java/android/location/LocationManager.java
4. GNSS 공급자 구현: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/location/gnss/GnssLocationProvider.java
5. Google GNSSLogger: https://github.com/google/gps-measurement-tools/blob/master/GNSSLogger/app/src/main/java/com/google/android/apps/location/gps/gnsslogger/AgnssFragment.java
6. Shizuku 권한 한계: https://shizuku.rikka.app/guide/setup/
7. Knox의 하드웨어 보안·Warranty Bit: https://docs.samsungknox.com/admin/fundamentals/whitepaper/samsung-knox-mobile-security/system-security/hw-backed-security/
8. 실제 GNSS 첫 측정 콜백: https://developer.android.com/reference/android/location/GnssStatus.Callback#onFirstFix(int)

AOSP는 안드로이드 기준 구현의 근거다. 삼성 펌웨어가 동일하게 구현됐다는 증거로 사용하지 않았다.

## 5. 실제 구현한 APK

패키지: `org.zetamesh.gnss`, 버전 0.1.0. 개인 설치용 개발 서명 APK다. Play Store 배포용 서명·심사는 수행하지 않았다.

- A: 보조정보 강제 요청 없이 GPS_PROVIDER를 시작한다.
- B: GPS_PROVIDER 시작 후 시간·PSDS 갱신 명령을 요청한다.
- C: B에 실제 네트워크 위치 요청을 추가한다. 네트워크 좌표를 GNSS fix로 세지 않는다.
- 최대 120초, 화면을 떠나면 중단. 활동 중에만 측정하고 종료 시 리스너·콜백·화면 유지 플래그를 해제한다.
- GNSS `onFirstFix`의 엔진 TTFF와 요청 이후 새 GPS 좌표 도착 시간을 따로 기록한다.
- 오래된 위치, 미래 시각, mock 위치, 시작 콜백이 없는 첫 측정, 중복 콜백을 제외한다. 엔진 TTFF가 앱 측정 경과시간보다 크게 앞서는 경우도 제외한다.
- 같은 GNSS 엔진을 다른 앱이 이미 쓰고 있을 가능성까지 이 필터만으로 배제할 수는 없다. 로그의 `engine_session_origin_verified`는 false다. `eligible_first_fix`는 기본 필터를 통과한 후보이며 cold start가 인증됐다는 뜻이 아니다.
- 정확한 위도·경도는 저장하지 않는다. 이벤트·시간·정확도·기기 빌드·네트워크 연결 여부·절전 상태를 JSONL로 저장한다. 내보내기는 사용자가 선택한 파일에만 수행한다.
- 수집기는 모드별 시도 수·유효 첫 측정 수·실패/제외 수·TTFF 중앙값/p95를 계산한다. 중단과 timeout도 시도 분모에 남긴다. 수집만으로 인과적 가속을 자동 판정하지 않는다.

Supabase·웹화면은 Android의 GNSS 권한을 해결하지 못한다. 이번에는 이 핵심 경로를 확인하는 독립 진단 앱을 먼저 적용했고, 기존 Supabase 서비스에는 위치 데이터나 가짜 측정값을 올리지 않았다.

## 6. 검증 결과와 실행 차단 사항

| 항목 | 결과 |
|---|---|
| Android SDK 35 / Build Tools 35.0.0 빌드 | 통과, `verification/build.txt` |
| 개발 APK 서명 검사 및 manifest 검사 | 통과 |
| Java 시험 상태·캐시·mock·시각 검사 | 통과, 실물 시험 아님 |
| JSONL 분석기 단위 검사 | 3개 통과, 시험 입력은 합성 fixture로 명시 |
| Fold3 설치·실행·UI 확인 | 미실행 |
| 삼성 PSDS 지원·실제 보조정보 주입 | 미확인 |
| 내장 GNSS TTFF 단축 | 미측정 |
| R4/BLE aiding 주입 | 구현·실측 경로 미확보 |

실제 빌드는 Linux 클라우드와 Python 3.11/JDK 21 환경에서 수행했다. SDK 압축파일은 공식 Google 배포 인덱스의 체크섬과 대조했다. SDK/도구 경로와 빌드 로그, APK SHA256은 `verification/`에 남겼다. Windows와 Fold3에서 실행한 결과가 아니다.

ADB 접근 시도는 이 클라우드의 읽기 전용 `/home/agent/.android` 때문에 daemon 시작이 실패했다. 사용자 PC의 USB 단말을 클라우드에 전달하는 연결도 제공되지 않았다. 이것은 Fold3의 USB·GNSS 고장을 의미하지 않는다. 사용자 PC에서 아래 설치 명령으로 재개할 수 있다. 부트로더·root·시스템 파티션·Knox 상태는 변경하지 않았다.

## 7. Fold3에서 적용하는 순서

1. `downloads/ZetaMesh-GNSS-Assist-debug.apk`를 휴대폰에서 내려받아 설치한다. Android가 출처 허용을 요청하면 해당 다운로드 경로에 필요한 설치만 허용한다. 조직 정책이 차단하면 정책을 우회하지 말고 개인 시험 단말에서 진행한다.
2. 앱의 정확한 위치 권한을 허용하고 휴대폰 위치 기능을 켠다. 인터넷이 되는 상태로 하늘이 열린 같은 장소에서 시험한다.
3. 다른 지도·내비게이션 앱을 종료하고 모의 위치 앱을 해제한다. 첫 시험은 A, 다음은 B로 수행해 앱과 로그가 동작하는지 먼저 확인한다. 이 두 번만으로 가속을 판정하지 않는다.
4. 각 시험의 종료·timeout을 기록하고 ‘실제 로그 내보내기’로 JSONL을 저장한다. 앱 삭제 전 내보낸다. 화면을 닫거나 잠그면 시험은 중단 처리된다.
5. 반복 시험은 A/B 순서를 균형 있게 바꾸고, 동일 장소·인터넷·절전 설정을 유지한다. C는 별도 조건으로 비교한다.

PC에서 USB 디버깅을 허용한 뒤 설치할 수도 있다.

```powershell
adb devices -l
adb install -r android\gnss-assist\downloads\ZetaMesh-GNSS-Assist-debug.apk
adb shell am start -n org.zetamesh.gnss/.MainActivity
py -3.11 android\gnss-assist\tools\analyze.py 실제로그.jsonl --out 실제로그_분석
```

설치가 서명 불일치로 거부되면 기존 앱의 로그를 먼저 내보내야 한다. 이 버전은 동일 개발 키로 만든 제공 APK이며, 사용자가 새 키로 재빌드한 APK는 기존 설치본과 서명이 달라질 수 있다. 개발 개인키는 저장소에 포함하지 않는다.

## 8. ‘실제로 빨라졌다’의 판정 조건

단순 A→B 반복은 A에서 받은 위성 정보가 B로 이월되어 B가 유리할 수 있다. B에서 갱신한 보조정보도 다음 A로 남는다. 대기하거나 위치 토글을 껐다 켠 것만으로 aiding cache가 완전히 초기화됐다고 가정하지 않는다.

첫 단계의 결과는 동일 환경에서의 warm/mixed-start 탐색 시험으로 보고한다. 가능하면 30쌍 이상을 모으고 성공률·timeout·엔진 TTFF·요청 이후 GPS fix 시간을 함께 비교한다. paired 시험 순서와 세션 조건은 따로 기록한다. 분석기는 실제 paired 세션이 확인되기 전에는 임의로 서로 다른 시도를 짝짓지 않는다.

엄격한 인과 검증에는 제조사에서 확인된 GNSS 상태 초기화·주입 확인 로그 또는 동일 상태를 재현할 수 있는 시험 절차가 필요하다. `delete_aiding_data`는 보조정보를 없애 오히려 초기 측위를 느리게 할 수 있으므로 현재 APK에서 자동 실행하지 않는다. 콜드 스타트 초기화를 추후 구현하더라도 삭제 성공 여부부터 검증해야 한다.

측정할 값은 보조정보 요청 전달 여부, 제조사 처리 근거, 기한 내 실제 GNSS fix 성공률, TTFF 분포와 실패율이다. API 반환 true나 앱 지도에 좌표가 뜨는 것만으로 성공 판정하지 않는다. 캐시가 이미 최신이면 개선이 없을 수 있으며 RF 차폐를 보조정보만으로 해결할 수 없다.

## 9. R4와 GPS 구매 판단, V1/V2 유지

일반 NEO 계열 모듈의 NMEA 위도·경도·시간 출력은 Fold3용 PSDS 데이터와 같은 것이 아니다. 수신기의 보조정보 형식·주입 인터페이스가 맞아야 하므로 ‘GPS 모듈 구매 → BLE 좌표 전송 → 내장 GNSS 가속’이 자동으로 성립하지 않는다. **지금은 GPS 모듈 구매를 보류하고 Fold3의 위 경로부터 확인하는 것이 합리적이다.**

V1 목표는 R4+GNSS → BLE → Fold3의 내장 GNSS 보조다. BLE 전달부와 안드로이드의 privileged aiding 연결부를 별도 기능으로 취급한다. 현재는 후자의 범용 경로가 미확보다.

V2 목표는 스마트폰 A가 R4의 정보 제공자 역할을 대체하고, 스마트폰 B가 수신하는 구조다. 같은 패킷 형식과 aiding 인터페이스 추상화를 유지할 수 있지만 두 일반 앱 사이의 BLE 연결만으로 B의 GNSS 권한 문제가 사라지지 않는다. 송신 좌표의 출처·나이·정확도·거리 조건과 수신 칩에 실제 적용 가능한 데이터 종류를 검증해야 한다.

루팅된 별도 시험 기기나 OEM 협력 경로에서는 신뢰된 앱/서비스가 BLE 데이터를 검증하고 실제 GNSS provider/HAL의 지원되는 aiding 함수로 전달하는 구성을 검토할 수 있다. 이는 Fold3 기본 펌웨어에서 이미 가능한 기능이 아니다. 삼성의 Knox Warranty Bit는 비공식 소프트웨어의 영향이 영구적으로 남을 수 있으므로 사용 중인 주 단말에 자동 적용할 단계가 아니다. 모델별 부트로더 지원 확인과 별도 시험 단말 계획이 선행되어야 한다.

## 10. 다음 작업과 완료 범위

이번 작업에서 조사 보고서, 실제 API 요청 코드, 설치용 APK, 빌드/서명 증거, 로컬 실제 로그 수집·분석기를 제공했다. 실물 TTFF 데이터는 0건이다. 실제 가속이나 BLE 기반 MVP 완료를 표시하지 않는다.

다음 순서는 제공 APK를 Fold3에서 실행 → 로그로 실제 버전·API 호출·GNSS 첫 측정 확인 → 삼성의 명령 처리 근거 확인 → 반복 시험으로 효과 판단이다. 이 경로가 무효이거나 외부 BLE 데이터를 반드시 칩에 넣어야 하면 OEM/시스템 통합 경로의 타당성을 검토한다. 웹 HTML/CSS·Supabase 저장·V1/V2 BLE 제품 화면은 이 핵심 적용 경로가 확인된 뒤 연동한다.
