# ZetaMesh — UNO R4 WiFi 실물 검증 시작

보유한 **UNO R4 WiFi 한 대**로 시작한다. 준비물은 보드, USB-C 데이터 케이블, 기존 Windows PC다. 이 단계는 추가 보드나 GPS 모듈 구매를 요구하지 않는다. 현재 소프트웨어는 가상 GNSS 표시를 붙인 메타데이터 패킷을 사용한다.

사용자의 R4 선택에 따라 실물 단계의 대상을 R4 WiFi로 바꾸었다. 기존 50노드 PC 시뮬레이션 조건은 유지한다. **R4 전력·지연·RF 실측은 아직 없다.** 코드 컴파일과 호스트 프로토콜 검사는 실제 보드 수신 검증과 구분한다.

## 1. 지금 실행하는 순서

1. 저장소 ZIP을 내려받아 압축을 푼다. `firmware/uno-r4-wifi/ZetaMeshR4/ZetaMeshR4.ino`를 Arduino IDE 2.x로 연다. `Config.h`, `Protocol.h`도 같은 폴더에 있어야 한다.
2. 보드 매니저에서 **Arduino UNO R4 Boards 1.6.0**을 설치한다. 라이브러리 매니저에서 **ArduinoBLE 2.1.0**을 설치한다. 의존 라이브러리 **Arduino_SpiNINA 0.0.2**도 함께 설치한다. 재현용 버전은 `toolchain-lock.json`에 있다.
3. 보드에서 **Arduino UNO R4 WiFi**와 실제 COM 포트를 선택한다. 이 스케치는 RA4M1 메인 MCU에 업로드한다. 통신용 ESP32-S3에는 Arduino의 연결 펌웨어를 사용한다.
4. 기본 `Config.h`는 `ZETAMESH_NODE_ID=1`, `ZETAMESH_ROLE=0`이다. 이 상태로 확인/컴파일 후 업로드한다.
5. 시리얼 모니터를 **115200 baud**로 연다. 모니터를 열기 전에 부팅 로그가 지나갈 수 있으므로 `i`를 보내 상태를 확인한다. 초기화가 성공하면 `ble_ready`, 실패하면 `ble_init_failed`가 기록된다.
6. `a` 한 글자를 전송한다. BLE 검색 앱에서 `ZetaMesh-R4-01` 또는 제조사 데이터의 `FF FF 5A 4D 01 01` 접두부를 확인한다. 이름은 스캔 응답에 있으므로 활성 스캔과 기기 목록 갱신이 필요할 수 있다.
7. `s`를 전송하고 `i`로 `mode=scan`을 확인한다. 주변 BLE 광고가 있으면 `scan_observations`를 관찰할 수 있다. 이 카운터는 RF 수신 프레임의 정밀 계수기가 아니다. 다른 ZetaMesh 송신기가 없으면 `received_virtual`은 0일 수 있다.
8. `c`로 3초 광고/3초 스캔 자동 진단으로 돌아간다. 이 코드의 광고는 비연결형으로 설정했다. 휴대폰에서는 연결 버튼 대신 광고 데이터를 확인한다.

휴대폰 BLE 검색은 광고가 실제로 보이는지 확인하는 첫 단계다. 휴대폰 검색 앱이 우리 패킷을 송신하거나 중계해 준다고 가정하지 않는다. 한 보드로 2홉 전달을 실증했다고 기록하지 않는다.

### 연결 펌웨어 점검

ArduinoBLE 공식 호환 표는 UNO R4 WiFi의 ESP32-S3 연결 펌웨어 **0.2.0 이상**을 요구한다. `ble_init_failed`가 반복되면 보드/포트 선택과 데이터 케이블을 먼저 확인하고, Arduino IDE의 **Tools → Firmware Updater** 및 공식 안내에 따라 연결 펌웨어 버전을 확인한다. 이 저장소에서는 보유 보드의 연결 펌웨어 버전을 읽거나 변경하지 못했다.

- 공식 지원 표: https://github.com/arduino-libraries/ArduinoBLE#firmware-compatibility
- 보드 공식 안내: https://docs.arduino.cc/hardware/uno-r4-wifi/

## 2. 시리얼 명령

모든 명령은 영문 소문자 한 글자다. 줄바꿈은 무시한다.

| 명령 | 기능 |
|---|---|
| `a` | 자기 가상 패킷을 광고하는 진단 모드 |
| `s` | 수신 진단 모드 |
| `c` | 광고/스캔을 3초마다 바꾸는 기본 진단 |
| `d` | Donor 역할로 전환 |
| `r` | Relay 역할로 전환. 수신한 유효 패킷이 없으면 탐색으로 복귀 |
| `k` | Seeker 역할로 전환 |
| `i` | 상태 JSON 출력 |
| `h` | 명령 도움말 출력 |

역할 변경은 RAM 상태를 초기화한다. 노드 ID는 `Config.h`에서 정하며 재부팅 후에도 같은 설정을 사용한다. 여러 보드에서는 서로 다른 ID를 지정해야 한다. 현재 기본값 1은 한 대 진단용이다.

## 3. 실제 로그 수집 — Windows

프로젝트 루트에서 다음을 실행한다. Arduino 시리얼 모니터를 닫은 뒤 수집기를 열어야 같은 COM 포트를 사용할 수 있다.

```powershell
py -3.11 -m venv .venv-r4
.\.venv-r4\Scripts\python.exe -m pip install -r firmware\uno-r4-wifi\requirements.txt
.\.venv-r4\Scripts\python.exe -m serial.tools.list_ports
.\.venv-r4\Scripts\python.exe firmware\uno-r4-wifi\tools\capture_serial.py --port COM5 --seconds 60 --out firmware\uno-r4-wifi\captures\r4-first --source-ref r4-0.1.0
```

`COM5`는 예시 포트이므로 실제 포트로 바꾼다. 소스 Git 커밋을 알고 있으면 `--source-ref`의 빌드 식별자를 그 커밋으로 바꿔 기록한다. 같은 출력 폴더는 덮어쓰지 않는다. 포트가 없으면 실패하고 데이터를 만들어 채우지 않는다. 유효 로그가 0행이면 종료 코드 2, 포트 오류로 일부만 수집되면 종료 코드 3으로 표시한다.

출력은 `serial_raw.bin`(원시 바이트), `raw.jsonl`(해석한 로그와 PC 수신시각), `events.csv`, `metadata.json`이다. 메타데이터에 PC의 실제 OS/Python·소스 참조·벽시계 시간·펌웨어 표시·무시한 줄 수를 남긴다. 시간은 UTC로 보존한다. 수집기는 물리 보드의 진위를 인증하지 않으므로 `physical_source_verified=false`를 기록한다. 전력은 측정하지 않는다.

`tx_updates`는 광고 데이터 설정 API의 갱신 횟수다. 이를 실제 송신 횟수나 에너지[J]로 환산하지 않는다. RSSI는 실제 ZetaMesh 수신 이벤트가 있을 때만 기록하며, GNSS 품질·배터리 SOC는 미측정이므로 `null`이다. 다른 BLE 기기의 이름·주소·위치는 로그에 저장하지 않는다.

## 4. 이후 3노드 시험 준비

보드를 추가하거나 빌릴 수 있을 때 같은 소스에 다음 설정을 적용한다. 지금 추가 구매를 전제하지 않는다.

| 보드 | NODE_ID | ROLE |
|---|---:|---:|
| A: Donor | 1 | 1 |
| B: Relay | 2 | 2 |
| C: Seeker | 3 | 3 |

목표 경로는 **A → B → C**다. Relay는 수신/광고 슬롯을 번갈아 사용하며 별도의 학습 정책 없이 신선한 패킷을 우선 보유하는 고정 기준선이다. 제타 선택·체비쇼프 추론은 아직 R4에 이식하지 않았다.

중계 검증 전 B를 끈 상태에서 A→C 직접 수신 여부를 같은 PHY/출력 조건으로 확인한다. B를 켠 뒤 동일 패킷 식별자의 중계와 C의 `hops=2`를 관찰한다. A→C가 직접 통신되는 배치에서 2홉 로그만 보고 범위 확장이라고 결론내리지 않는다. 소프트웨어에서 A 패킷을 숨겨 직접 링크 실패를 꾸미지 않는다.

한 대에서 코드가 컴파일되는 것과 3대에서 무선 전달이 동작하는 것은 다른 증거다. 실제 직접 링크 실패·2홉 성공·RSSI·전력·지연은 후속 측정 대상이다. 이는 자체 BLE 광고 중계이며 Bluetooth Mesh 표준 스택 구현이 아니다.

## 5. 패킷과 시간 규칙

제조사 데이터 본문은 **26바이트**, flags와 AD 헤더를 포함한 광고 데이터는 **31바이트**다. 별도 서비스 UUID를 광고에 넣지 않는다. 기기 이름은 스캔 응답에 둔다. 전체 PHY 패킷 길이와 스캔 요청/응답 오버헤드는 별도이며 31바이트에 포함되지 않는다.

리틀엔디언 고정 프레임: 시험용 company ID `0xFFFF`, magic `ZM`, version 1, 종류 `virtual_gnss`, 원본/송신 노드, 부팅 식별자, sequence, 원본 생성 시각, 누적 age, lifetime, hops/max_hops, 품질/배터리, CRC-16/CCITT-FALSE다. `Protocol.h`의 바이트 오프셋이 구현 기준이다.

- 현재 패킷은 위성 보조정보 본문을 담지 않는 **가상 메타데이터**다. 실제 위치 수집·A-GNSS 주입·TTFF 단축을 검증하지 않는다.
- source_created_ms는 **원본 보드의 부팅 후 시각**이다. 다른 보드의 millis()나 PC 시각과 직접 빼서 전달 지연을 계산하지 않는다. 로그의 hops는 수신 노드까지 완료된 홉 수다.
- 상대 수명 24초와 공통 최대 홉 4를 사용한다. 누적 age가 lifetime에 도달하면 무효이며 32비트 millis() 순환은 상대 차이로 처리한다.
- 광고 간격 요청값은 200ms이며, 광고 내용을 500ms마다 갱신하고 각 송신 때 age에 1000ms의 보수적 보정값을 더한다. 갱신은 광고 재시작을 포함하므로 갱신 사이에 요청 광고 간격이 들어가도록 설정했다. 실제 간격과 이 보정값·HCI 호출 지연의 상한은 미실측이다. 펌웨어/컨트롤러가 오래 지연되는 상황까지 실제 RF 만료를 보장했다고 주장하지 않는다.
- 중복 캐시는 16개다. 이 코드는 실물 소수 노드용이고 50개 실물 노드 처리 규모를 검증하지 않았다.
- 버전·길이·CRC·ID·시간·홉·범위를 검사하고 오류 프레임을 무시한다. 품질·배터리 255는 결측값이다. CRC와 시험용 부팅 nonce는 암호 인증이나 영구 유일성을 제공하지 않는다.
- `0xFFFF`는 실험용 표기로만 사용하며 상용 배포 전 정식 제조사 데이터 식별 정책을 정해야 한다.

## 6. 재현 빌드와 검사

Arduino CLI 1.5.1에서 실행한 명령과 버전은 `toolchain-lock.json` 및 `validation/`에 기록한다. 아래 CLI 명령은 Windows에서도 동일한 인자를 쓸 수 있다. 클라우드에서는 별도 config 파일로 도구 경로와 제공된 프록시를 지정했다.

```text
arduino-cli core update-index
arduino-cli core install arduino:renesas_uno@1.6.0
arduino-cli lib install Arduino_SpiNINA@0.0.2 ArduinoBLE@2.1.0
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --jobs 2 --warnings all firmware/uno-r4-wifi/ZetaMeshR4
```

호스트 프로토콜 검사와 수집기 검사는 다음과 같다. C++ 검사는 호스트 C++11 컴파일러가 있을 때 실행한다.

```text
g++ -std=c++11 -Wall -Wextra -Werror -pedantic firmware/uno-r4-wifi/tests/protocol_test.cpp -o protocol-test
./protocol-test
python -m unittest discover -s firmware/uno-r4-wifi/tests -p "test_*.py" -v
```

GitHub Actions의 **UNO R4 WiFi 펌웨어 검증**은 네 역할을 각각 빌드하고 빌드 산출물을 보관한다. 바이너리 빌드는 실제 업로드·RF 수신을 실행하지 않는다. 앱 소스의 확정 버전은 해당 실행의 Git 커밋으로 추적한다.

## 7. 기존 연구 결과와의 관계

50노드의 세 시나리오·30개 평가 시드 조건은 기존 PC 시뮬레이션에 유지한다. 이번 R4 단계에서는 50노드 평가를 새로 실행하지 않았다. 기존 에너지 절감 결과는 가정 전력 기반 Linux 시뮬레이션이며 R4 전력 측정값이 아니다. 기존 통합 정책은 성공률 조건을 만족하지 못했다.

R4 WiFi는 RA4M1과 ESP32-S3 및 보드 회로를 함께 사용하므로 ESP32-C3의 전류 가정을 그대로 옮길 수 없다. 실제 보드 전체 전류·스캔/광고 동작·Wi-Fi/LED 등 주변 회로 상태를 먼저 기록해야 한다. ArduinoBLE의 스캔창·채널 제어·연결 펌웨어 내부 동작도 현재 PC 물리 모형과 교차 검증하지 않았다.

컴파일 출력의 Flash/정적 RAM은 RA4M1 스케치에 대한 값이다. 실행 중 heap/stack의 최고 사용량, ESP32-S3 연결 펌웨어 메모리, 보드 전력·GNSS 소비전력은 포함하지 않는다.

## 8. 현재 남은 검증

사용자 Windows PC에서 업로드 → `ble_ready` → 휴대폰에서 광고 확인 → 실제 시리얼 로그 수집 순서로 진행한다. 이후 실제 노드를 확보할 때 직접 링크와 2홉 전달, 전력, 시간 동기화, GNSS 수집/주입을 별도로 검증한다. 실제 로그를 받기 전에는 예시 RSSI·전류·전달 성공률을 결과로 쓰지 않는다.
