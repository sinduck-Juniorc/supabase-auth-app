# 에코 트레킹 BLE 0·1 시연

UNO R4 WiFi에서 BLE 알림으로 한 바이트를 보내면 Android 앱이 `0` 또는 `1`을 크게 표시한다.

## R4 준비

1. Arduino IDE에서 [EcoTrekkingBinaryDemo.ino](../../firmware/uno-r4-wifi/EcoTrekkingBinaryDemo/EcoTrekkingBinaryDemo.ino)를 연다.
2. [R4 도구 체인](../../firmware/uno-r4-wifi/README.md)을 준비하고 **Arduino UNO R4 WiFi**와 해당 보드의 USB 포트를 선택한다. 업로드하면 보드에 들어 있던 스케치가 교체된다.
3. **도구 → 시리얼 모니터**를 열어 `115200 baud`를 선택한다. 시리얼 모니터는 Arduino IDE 안의 보드 전용 터미널이다.

## Android 앱 준비

GitHub Actions의 **에코 트레킹 Android 시연 빌드**에서 `Eco-Trekking-BLE-Demo` 아티팩트를 내려받고 ZIP의 `Eco-Trekking-BLE-Demo.apk`를 설치한다. 로컬의 SDK 35와 JDK 17이 있는 경우 저장소 루트에서 아래처럼 빌드할 수 있다.

```powershell
python .\android\gnss-assist\tools\build.py --demo --sdk "$env:LOCALAPPDATA\Android\Sdk" --keystore .\.local\eco-trekking-demo.keystore
adb install .\android\gnss-assist\build\demo\Eco-Trekking-BLE-Demo.apk
```

시연 앱 패키지는 `org.zetamesh.ecotrekking.demo`다. GitHub Actions는 실행마다 임시 키를 사용하므로, 이전 빌드와 서명이 다르면 같은 키로 서명한 APK가 필요하다. Android 11에서는 위치 권한과 위치 서비스가 필요할 수 있으며, Android 12 이상에서는 앱의 근처 기기 권한을 허용한다.

## 시연 순서

1. 스마트폰에서 Bluetooth를 켜고 **에코 트레킹 BLE 시연** 앱을 연다. **R4 연결**을 누르고 `R4 연결됨` 표시가 뜰 때까지 기다린다.
2. 시리얼 모니터 입력 칸에 `1`을 보내면 앱에 **1**이 표시된다. 이어 `0`을 보내고 **0**으로 바뀌는지 확인한다. 줄바꿈 설정과 관계없이 R4는 ASCII 숫자 `0`·`1`만 처리한다.
3. 앱을 화면에서 벗어나거나 연결이 끊기면 숫자 표시를 초기화한다. 앱에서 **R4 연결**을 눌러 다시 시험한다.

Bluetooth GATT 알림으로 동작하는 1홉 시연이다. Wi‑Fi·메시 중계·전력 절감은 이 시연의 측정 항목에 포함되지 않는다. 모뎀 AT 명령은 사용하지 않는다.
