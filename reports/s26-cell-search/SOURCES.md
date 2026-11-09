# 조사 근거 목록

조사일 2026-11-09. 공개 1차 자료와 기존 저장소 자료를 구분했다. 외부 조사 종료 시각은 evidence/research-freeze.json 참조. 이 목록은 종료 전에 확보한 자료의 정리이며 추가 조사가 아니다.

## S01 · 삼성전자서비스 국내 출시 사양

[삼성전자서비스 국내 출시 사양](https://www.samsungsvc.co.kr/solution/4613052)

SM-S947N, Exynos 2600, Android 16 / One UI 8.5 출시 사양. 국가별 차이. 표 설명에 S24 편집 잔재.

## S02 · 삼성 SM-S947B 업데이트 이력

[삼성 SM-S947B 업데이트 이력](https://doc.samsungmobile.com/SM-S947B/037203260310/eng.html)

조사 시 상단 S947BXXU5BZJA, 2026-10-29, Android 17. 2026-09-30 One UI 9 항목. 사용자 단말 버전으로 전이하지 않음.

## S03 · 삼성 글로벌 S26 발표

[삼성 글로벌 S26 발표](https://news.samsung.com/global/samsung-unveils-galaxy-s26-series-the-most-intuitive-galaxy-ai-phone-yet)

2026-02-26 발표. AP의 국가·지역 차이를 구분.

## S04 · 기존 클라우드 Fold3 보고서

[기존 클라우드 Fold3 보고서](https://github.com/sinduck-Juniorc/supabase-auth-app/blob/eb12bf5a1df8aae8922129fb01760138c298af4e/android/gnss-assist/REPORT_ko.md)

실제 작성된 코드·검증 로그 참고. 실물 Fold3 성능 자료가 아님.

## S08 · Android TelephonyManager

[Android TelephonyManager](https://developer.android.com/reference/android/telephony/TelephonyManager)

requestCellInfoUpdate와 requestNetworkScan의 의미·권한 구분.

## S10 · Android NetworkScanRequest

[Android NetworkScanRequest](https://developer.android.com/reference/android/telephony/NetworkScanRequest)

무선 방식·대역·채널·망 식별자 입력. 좌표 직접 입력과 다름.

## S12 · AOSP UICC carrier privileges

[AOSP UICC carrier privileges](https://source.android.com/docs/core/connect/uicc)

SIM 인증서 규칙과 앱 서명에 기반한 일부 특별 API 접근. 통신사 협력 경로.

## S13 · Shizuku 공식 사용 설명

[Shizuku 공식 사용 설명](https://shizuku.rikka.app/guide/setup/)

root, 무선 디버깅, PC ADB 시작 방법과 ADB 권한 제한 안내.

## S14 · ETSI TS 38.304 V18.6.0

[ETSI TS 38.304 V18.6.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138304/18.06.00_60/ts_138304v180600p.pdf)

2026-04판. 인쇄 17~21쪽, 5.1.1.2 및 5.2.3.1. 저장 주파수·셀 정보 사용, 실패 시 초기 탐색. Android 권한 문서가 아님.

## S05 · AOSP 소스

- [location_service](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/location/LocationManagerService.java) · 조회 2026-11-09T21:45:00.020749+09:00 · SHA-256 `5b91c7605b78cc9e031020d9dc69e7ba71d014860be930932b73b6fb73a3ebaf`

- [location_manager](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/location/java/android/location/LocationManager.java) · 조회 2026-11-09T21:44:12.309494+09:00 · SHA-256 `524337e366915cb45143f5a75d2fff6983b51c468a4606ab431af95da739c487`

## S06 · AOSP 소스

- [gnss_provider](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/location/gnss/GnssLocationProvider.java) · 조회 2026-11-09T21:44:12.254558+09:00 · SHA-256 `7555e1f546a89bc993005cdad585a9dbe8ecb1e886f14ae858d7b71e5155d3c4`

## S07 · AOSP 소스

- [gnss_aidl](https://android.googlesource.com/platform/hardware/interfaces/+/refs/heads/main/gnss/aidl/android/hardware/gnss/IGnss.aidl) · 조회 2026-11-09T21:45:00.031423+09:00 · SHA-256 `a59abefd2d938e49c26a2a593599d7c129cc212f5e789aa984d4ad02fe4bcd17`

## S09 · AOSP 소스

- [phone_service](https://android.googlesource.com/platform/packages/services/Telephony/+/refs/heads/main/src/com/android/phone/PhoneInterfaceManager.java) · 조회 2026-11-09T21:45:00.381208+09:00 · SHA-256 `2e908a747570bccfa6ab5e7d967ac800e319d940d12b4621a3f7f0a35380c6a4`

## S10 · AOSP 소스

- [network_scan_request](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/telephony/java/android/telephony/NetworkScanRequest.java) · 조회 2026-11-09T21:44:12.533048+09:00 · SHA-256 `d2bc5d79f81d7a30f4d26b00cd090e8deaab5982417313e3b997cda7c3b601c9`

- [telephony_hal](https://android.googlesource.com/platform/hardware/interfaces/+/refs/heads/main/radio/aidl/android/hardware/radio/network/IRadioNetwork.aidl) · 조회 2026-11-09T21:45:00.717938+09:00 · SHA-256 `bc3f6892af9bc416d4951a3a27b15d1f35146618760486bf13a19cc8a9a0f53e`

## S11 · AOSP 소스

- [shell_manifest](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/packages/Shell/AndroidManifest.xml) · 조회 2026-11-09T21:44:12.266534+09:00 · SHA-256 `9779778e85fbb5c9ac30555c4a41bdce16245d93d4704d880f4b92166a56725f`

- [permissions](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/res/AndroidManifest.xml) · 조회 2026-11-09T21:44:12.475480+09:00 · SHA-256 `336cc3ed0c0182b9a6d9345f6003e042285b9bfbd67d74c5c5959d01186280fc`

## S08 · AOSP 소스

- [telephony](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/telephony/java/android/telephony/TelephonyManager.java) · 조회 2026-11-09T21:44:12.893236+09:00 · SHA-256 `125e4e94103d72fd5b2f775088ccb7b0aaa0c11b1a844da734effdd10d102eb8`


AOSP는 main 브랜치 조회본이다. Android 16/17 삼성 제품 코드와 일치한다는 보장은 없다. 참고용 전체 다운로드 목록에는 최종 판단에 사용하지 않은 파일도 포함한다. 표준·삼성 웹페이지의 전체 원문은 재배포하지 않으며, 본문에 확인 사실과 한계를 요약했다.
