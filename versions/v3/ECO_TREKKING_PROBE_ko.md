# 에코 트레킹 Android 계측 실행

## 준비

V3 개발 APK를 [기존 빌드 절차](../../android/gnss-assist/README.md)로 다시 빌드한다. 기존 V2 APK에는 이 명령이 없다. SDK 35, JDK 17 이상과 로컬 개발 키를 사용한다. APK와 키는 로컬에 둔다. V3가 이미 설치되어 있다면 같은 키로 서명해야 업데이트 설치할 수 있다.

저장소 루트에서 PowerShell을 열고 USB 디버깅을 승인한 기기 한 대를 연결한다. `adb`가 PATH에 없으면 `$adb`에 PC의 실제 `adb.exe` 경로를 넣는다.

```powershell
$adb = 'adb'
& $adb install -r .\android\gnss-assist\build\ZetaMesh-V3-dev.apk
& .\versions\v3\tools\Invoke-EcoTrekkingProbe.ps1 -Adb $adb -Mode battery
```

동일한 배터리 조회를 직접 실행하는 명령이다.

```powershell
& $adb shell am instrument -w -r -e mode battery org.zetamesh.gnss.v3/org.zetamesh.gnss.TrekkingProbe
```

`charge_uah`, `energy_nwh`, `battery_percent`가 기기에서 지원되는지 확인한다. `unsupported`는 해당 항목을 읽을 수 없다는 뜻이다. 실제 배터리 비교에서는 USB 충전과 무선 충전을 분리하고 Android 무선 디버깅으로 시작·종료 값을 읽는다. 두 표본의 `external_power=no`를 확인하고 측정 중에도 충전이 연결되지 않도록 한다. 전하 감소량(mAh)은 (시작 µAh − 종료 µAh) / 1000이고, 에너지 감소량(mWh)은 (시작 nWh − 종료 nWh) / 1,000,000이다. 단말 전체의 감소량이며 개별 앱 전력계 값은 아니다. 트래킹을 시작하기 전과 종료한 후에 이 명령을 실행한다. 인스트루먼테이션이 실행 중인 V3 프로세스를 재시작할 수 있다. [Android BatteryManager](https://developer.android.com/reference/android/os/BatteryManager) · [ADB 무선 디버깅](https://developer.android.com/tools/adb#wireless)

## 폰↔UNO R4 WiFi BLE 1홉

1. [별도 에코 스케치](../../firmware/uno-r4-wifi/EcoTrekkingEcho/EcoTrekkingEcho.ino)를 Arduino IDE에서 연다. 기존 [R4 도구 체인](../../firmware/uno-r4-wifi/README.md)으로 컴파일하고 UNO R4 WiFi에 업로드한다. 보드에서 기존 ZetaMesh 스케치를 교체하는 단계이며, 기존 스케치는 같은 도구 체인으로 다시 올릴 수 있다.
2. 휴대폰의 Bluetooth를 켠다. S26+에서 아래 명령으로 V3 시험 앱의 근처 기기 권한을 부여한다. Android 11에서는 `ACCESS_FINE_LOCATION` 권한과 위치 서비스가 필요하다.

```powershell
& $adb shell pm grant org.zetamesh.gnss.v3 android.permission.BLUETOOTH_SCAN
& $adb shell pm grant org.zetamesh.gnss.v3 android.permission.BLUETOOTH_CONNECT
& .\versions\v3\tools\Invoke-EcoTrekkingProbe.ps1 -Adb $adb -Mode ble -Count 20
```

직접 실행하는 명령이다.

```powershell
& $adb shell am instrument -w -r -e mode ble -e count 20 org.zetamesh.gnss.v3/org.zetamesh.gnss.TrekkingProbe
```

폰이 매번 새 순번을 써서 UNO R4의 GATT 특성에 보낸 뒤 같은 값을 읽어 비교한다. `complete=true`이면 일치 성공률은 `matched / requested`다. `round_trip_p50_us`와 `round_trip_p95_us`는 일치한 응답의 쓰기 시작→읽기 완료 지연이다. 연결 탐색 시간은 포함하지 않는다. 통신 오류나 단계별 5초 시간 초과가 발생하면 시험을 중단하고 시도 수와 오류를 출력한다. 이 경우 전체 요청 수를 다 실행한 측정과 구분한다. 시험은 GATT 1홉 왕복을 평가한다. 무선 광고 전달률, 다중 홉 메시 또는 Wi‑Fi 성능은 별도 시험이 필요하다. [Android Bluetooth 권한](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions)

이 도구는 모뎀 COM 포트를 열거나 AT 명령을 보내지 않는다. S26+와 UNO R4 실기기 검증은 아직 진행되지 않았다.
