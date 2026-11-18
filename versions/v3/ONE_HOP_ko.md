# 에코 트레킹 1홉 광고 시연

## 수신 로그

[수신 로그 앱 0.2.0 다운로드](https://github.com/sinduck-Juniorc/supabase-auth-app/actions/runs/44221604949/artifacts/14391061941)

**에코 트레킹 1홉 로그** 앱에서 **1홉 수신 시작**을 누르면 로그를 자동 기록한다. 측정이 끝나면 **저장 후 종료**를 눌러 폴더를 선택한다. 파일 쓰기에 성공하면 앱이 닫힌다. **로그 내보내기**는 같은 파일을 저장하고 앱 화면을 유지한다. 두 버튼 모두 파일 위치를 고르기 전에 현재 수신 세션을 종료한다. 취소하거나 저장에 실패하면 내부 기록에서 다시 내보낼 수 있다.

`eco-trekking-one-hop-*.jsonl`은 UTF-8로 저장하며 각 줄은 JSON 객체 하나다. 앱에 누적된 세션들은 `session_id`로 구분한다. 수신 이벤트의 `digit`, `sequence`, `sender_boot_id`, `rssi_dbm`, `received_elapsed_ms`, `remaining_ttl_ms`와 종료 요약의 수신·무효·만료·중복/역순 개수를 분석할 수 있다. `unix_ms`는 폰의 기록 시각이다. 로그에는 원본 무선 패킷, 기기 Bluetooth 주소, 좌표를 저장하지 않는다.

전달률을 계산하려면 R4에 몇 번 입력했는지 따로 남긴다. 폰 기록만으로 미수신 송신 시도 수나 R4의 광고 주기 전환을 모두 확인할 수 없다. 기존 시연 APK와 로그 추가 APK는 서로 다른 패키지를 사용하므로 함께 설치할 수 있다.

### 로그 APK 실물 시험

1. 폰에서 **에코 트레킹 1홉 로그** 앱의 **1홉 수신 시작**을 누른다. R4에 `EcoOneHop`이 올라가 있다면 기존 스케치를 그대로 사용한다.
2. Arduino IDE의 시리얼 모니터를 닫고 아래 명령으로 R4에 `0 → 1 → 0 → 1`을 보낸다. 폰에 값이 표시되는지와 관계없이 PC가 각 입력을 3초 간격으로 전송한다.
3. 폰에서 **저장 후 종료**를 누르고 기기 내부 저장소의 폴더를 선택한다. 저장이 완료된 뒤 앱 화면이 닫히는지 확인한다. 폰의 파일 앱에서 생성된 JSONL을 확인한다. PC에서 검사할 때는 개인 원본을 Git이 제외하는 `captures/v3/`에 둔다.
4. 이번 `session_id`의 `session_start`부터 `session_end`까지 확인한다. 네 번 모두 수신했다면 `packet_received`의 `digit`은 `0 → 1 → 0 → 1` 순이고 같은 `sender_boot_id`에서 `sequence`가 진행한다. 종료 행의 `reason`은 `save_and_exit`이며 `received_count`는 해당 세션의 `packet_received` 행 수와 일치해야 한다. 종료 행과 별도로 앱 화면이 실제로 닫혔는지 기록한다.

Windows에서 저장소 루트를 열고 실행한다. `COM3`은 `--list`에서 확인한 UNO R4 WiFi 포트로 바꾼다. `pyserial`이 필요한 경우 `python -m pip install -r firmware/uno-r4-wifi/requirements.txt`로 설치한다. 포트 목록은 Arduino의 보드 정의에 있는 USB ID를 사용한다. [UNO R4 WiFi 보드 정의](https://github.com/arduino/ArduinoCore-renesas/blob/main/boards.txt#L98-L117)

```powershell
python versions/v3/tools/send_one_hop_digits.py --list
python versions/v3/tools/send_one_hop_digits.py --port COM3
```

115200 baud로 포트를 열고 2초 뒤 첫 입력을 보낸다. 출력 시간은 첫 쓰기 시작을 기준으로 한 PC 경과 시간이다. 쓰기 성공 행으로 PC 입력 시도 수를 세고, 폰 JSONL의 순번으로 확인된 수신 수를 센다. 실제 BLE 광고 시각은 별도 측정이 필요하다.

PC에서 JSONL 문법을 확인하려면 저장소 루트에서 다음을 실행한다. 경로는 옮겨 놓은 파일 이름에 맞춘다. 이 명령은 로그 내용을 출력하지 않는다.

```powershell
Get-Content -LiteralPath 'captures/v3/eco-trekking-one-hop-실제파일명.jsonl' -Encoding UTF8 -ErrorAction Stop |
  ForEach-Object { $null = ConvertFrom-Json -InputObject $_ -ErrorAction Stop }
```

## 초기 시연 자료

[에코 트레킹 1홉 APK 및 Arduino 스케치 ZIP 다운로드](https://github.com/sinduck-Juniorc/supabase-auth-app/actions/runs/44218457506/artifacts/14389013826)

GitHub Actions의 **에코 트레킹 Android 시연 빌드**에서 `Eco-Trekking-OneHop` ZIP을 받는다. 압축 안의 `Eco-Trekking-OneHop.apk`를 스마트폰에 설치하고, `EcoOneHop` 폴더 전체를 유지한 채 Arduino IDE에서 `EcoOneHop.ino`를 열어 UNO R4 WiFi에 업로드한다. 보드와 라이브러리는 [R4 준비 절차](../../firmware/uno-r4-wifi/README.md)를 따른다. 업로드하면 보드에 있던 스케치가 교체된다.

1. 휴대폰의 Bluetooth를 켜고 **에코 트레킹 1홉 → 1홉 수신 시작**을 누른다. 근처 기기 권한을 허용하고 화면을 열어 둔다.
2. Arduino 시리얼 모니터를 115200 baud로 열고 `1`을 보낸다. 폰에 1과 순번이 표시되면 `0`을 보내 숫자가 바뀌는지 확인한다. 같은 값을 다시 입력해도 순번이 증가한다. 연속 입력이 쌓이면 가장 최근 값이 우선한다.
3. R4에서 폰의 존재 광고를 관측한 뒤 시리얼 모니터에 `scan=60/600 burst=1600ms`가 뜨는지 확인한다. 데이터가 오래되거나 주변 후보가 사라지면 기본 주기로 돌아간다. 폰은 데이터 유효 기간이 지나면 숫자를 지운다.

## 연구 방식의 적용 범위

R4를 원본 노드, 스마트폰을 수신 노드로 두었다. 폰은 존재를 알리는 짧은 광고를 보내고 R4는 숫자를 제조사 데이터 광고에 직접 담는다. 양방향 모두 같은 두 기기 사이에서 동작한다. 실험용 회사 코드, ZM 식별자, 전용 패킷 종류, 부팅 식별자·순번, 정보 나이·수명, 홉 제한과 CRC를 사용한다. 폰은 원본 R4의 홉 0·제한 1인 패킷을 한 번만 채택한다. 이 프레임은 숫자 시연용으로 정의했다.

R4는 [등산로 설정](../../research/ZetaMesh50/configs/50nodes_mountain.yaml)과 [결합 정책의 주기 결정](../../research/ZetaMesh50/policies/combined.py)을 적용한다. 최근 5초 이내 폰을 관측했고 데이터 나이가 15초 미만이며 첫 광고 요청이 처리됐을 때, 600ms당 목표 스캔 창을 180ms에서 60ms로 줄이고 데이터 광고 묶음 간격을 800ms에서 1600ms로 늘린다. 데이터 수명은 24초다. 새 입력은 즉시 송신을 시도한다. 광고 성공은 R4의 로컬 API 결과이며 수신 확인은 폰의 표시로 한다.

하나의 무선 장치가 송수신을 번갈아 수행하므로 R4는 160ms 송신 구간 안에서 40ms 광고 간격을 요청하고 겹치는 스캔 시간은 송신에 양보한다. 이 수치는 스케줄 목표이며 실제 전파 송출 시점이나 배터리 측정값은 미확인이다. Android 쪽은 전경 스캔과 존재 광고를 사용한다.

후보가 한 대일 때 제타 가중 선택 확률은 1이며 체비쇼프 점수로 순위가 바뀌지 않는다. 이 앱에는 다중 후보 점수 계산과 제3 기기로의 재광고를 넣지 않았다. 실제 중계는 송신기·중계기·수신기가 있는 2홉에서 검증해야 한다. 이번 시험은 독자 광고 방식의 첫 홉을 검증하는 용도다.
