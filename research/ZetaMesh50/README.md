# ZetaMesh50 — 50개 가상 BLE 노드 연구

밀집 성공률 개선판: [독립 평가 보고서](revisions/dense90/REPORT_ko.md). 밀집 설정의 `slow_adv_s`만 1.6→0.8초로 수정했다. 제타·체비쇼프 및 시뮬레이터 코드는 그대로다. 아래 기존 1000~1029 평가 안내와 `reports/`는 수정 전 연구 기록이며, 현재 설정의 새 평가는 2000~2029를 사용한다. 수정 전 밀집 설정은 `revisions/dense90/configs/original.yaml`에 보존했다.

이 프로젝트는 **자체 BLE 광고 중계 프로토콜의 이벤트 시뮬레이터**다. 표준 Bluetooth Mesh 구현·실제 A-GNSS 주입·TTFF 실증이 아니다. 대상은 Windows / Ryzen 5 5600X / RAM 32GB / Python 3.11 x64 / CPU이며 GPU나 신규 장비를 요구하지 않는다.

실제 실행 환경은 Linux 클라우드의 Python 3.11.17, AMD EPYC, CPU 할당 약 2코어, RAM 한도 8GiB였다. 따라서 실제 실행은 2프로세스다. Windows 5600X 성능으로 해석하면 안 된다. 실물 ESP32-C3 장치는 연결되지 않았다.

## 파일

- `configs/50nodes_{mountain,urban,dense}.yaml`: 각 50노드, 90초, 정책 공통 PHY/주기 범위/트래픽/전력 가정.
- `simulator/{events,topologies,radio,energy,packet,network,metrics,runtime}.py`: 이벤트 큐·이동·3개 광고 채널·상호 배타 에너지 상태·패킷·중계·원자료·환경 기록.
- `policies/{fixed,random,greedy,zeta,chebyshev,combined}.py`: 6개 필수 정책과 단순 threshold/LUT. 정책은 `combined.py`의 공통 인터페이스로 동작한다.
- `training/fit_quality.py`: 합성 품질 회귀, 3/5/7차와 선형/LUT/결정트리/작은 MLP 비교. RL은 포함하지 않았다.
- `models/`: 계수, 분리된 회귀 원자료, 실제 PC 추론 시간과 오차 표.
- `scripts/{run_experiment,freeze_design,sensitivity,make_report}.py`: 반복 실험·사전 기준선 동결·민감도·통계/그림/한국어 보고서.
- `tests/test_core.py`: 필수 수학·패킷·채널·중계·에너지·재현성 검증 26개.
- `outputs/`: 실행별 CSV·설정/환경 manifest·실행 당시 소스 스냅샷.
- `reports/evaluation_design_ko.md`, `reports/preregistration.json`: 평가 전 설계와 튜닝으로 동결한 기준선.
- `reports/50node_validation_ko.md`, `reports/*.csv`, `reports/figures/`: 최종 보고서·요약·paired 차이/신뢰구간·그림.
- `docs/`: 첨부 문서 원본. 연구 범위는 50노드 실행 명세를 우선한다.
- `logs/`: 실제 설치·검증·실험 로그. `benchmarks/`: 병목 프로파일.
- `firmware/esp32c3/README_ko.md`: 아직 실행하지 않은 실물 검증 절차. 실행 가능한 펌웨어는 아니다.

## Windows 설치

아래 명령은 프로젝트 루트의 PowerShell에서 실행한다. 활성화 스크립트를 쓰지 않아 실행 정책 변경이 필요 없다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

`requirements.txt`는 직접 의존성, `requirements-lock.txt`는 실제 Linux 3.11 설치 전체, `requirements-windows-lock.txt`는 같은 버전을 토대로 Windows 3.11 바이너리 패키지 해석까지 확인한 고정 목록이다. **Windows에서 설치·실행한 증거는 아니다.** PyYAML을 명시했다. 사용자 PC에서는 pip check 결과를 다시 확인한다. SimPy 대신 자체 heap 이벤트 큐를 사용하며 이번 범위에 필요 없는 PyTorch/Optuna/Gymnasium은 설치하지 않는다.

## 순차 동작 검증과 재현

배포된 `outputs/`는 실제 결과다. 기존 실행을 덮어쓰지 않도록 새 출력 디렉터리를 지정한다. 평가 시드는 사전 동결된 1000~1029이고 `--phase evaluation`은 50노드와 최소 30시드를 강제한다.

```powershell
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase smoke --nodes 3 --policy fixed --seeds 1 --seed-start 10 --workers 1 --out outputs/replay_smoke3
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase smoke --nodes 10 --policy fixed --seeds 1 --seed-start 10 --workers 1 --out outputs/replay_smoke10
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase evaluation --seeds 30 --seed-start 1000 --workers 4 --out outputs/windows4
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase evaluation --seeds 30 --seed-start 1000 --workers 6 --out outputs/windows6
.\.venv\Scripts\python.exe -m scripts.make_report --input outputs/windows4
```

대상 PC는 4프로세스로 시작한다. 작업 관리자와 manifest/runs.csv에서 여유를 확인한 뒤 6개와 비교한다. 초기 RAM 목표는 20~24GB 이하다. 실험 중 PC의 다른 작업을 기록한다. `make_report`는 `reports/`를 다시 생성하므로 보존할 보고서는 먼저 별도 폴더에 복사한다.

Linux 실제 실행 진입점은 다음과 같았다. Python 경로는 프로젝트 외부의 로컬 가상환경이었다.

```bash
/workspace/work/.venv/bin/python -m pytest -q
/workspace/work/.venv/bin/python -m training.fit_quality
/workspace/work/.venv/bin/python -m scripts.run_experiment --phase tuning --seed-start 200 --seeds 5 --workers 2 --out outputs/tuning
/workspace/work/.venv/bin/python -m scripts.freeze_design
/workspace/work/.venv/bin/python -m scripts.run_experiment --phase evaluation --seed-start 1000 --seeds 30 --workers 2 --out outputs/evaluation
/workspace/work/.venv/bin/python -m scripts.sensitivity --workers 2
/workspace/work/.venv/bin/python -m scripts.make_report
```

현재 프로젝트에는 `preregistration.json`이 이미 있으므로 `freeze_design`은 재동결을 거부한다. 본 결과를 재현할 때는 동결된 기준선을 그대로 사용한다. 새 연구를 설계하려면 프로젝트를 새 디렉터리로 복사하고 기존 outputs와 동결 파일을 보관한 뒤, **평가 전에** 설계 문서와 학습/튜닝/평가 시드를 새로 정한다. 본 평가를 본 뒤 기준선을 바꾸지 않는다.

## 동작과 공정성

모든 정책은 같은 1M 가정 PHY, 0dBm, hop limit 4, 3개 legacy 광고 채널, 스캔 윈도우 범위 40~210ms/간격 600ms, 광고 간격 범위 0.4~2.0초를 공유한다. 초기 발견은 기본 180ms/600ms 스캔과 0.8초 광고다. `combined`, `threshold`, `lut`는 유효 정보를 보유하고 요청이 없으며 관측 후보가 있을 때 60ms 스캔으로 전환한다. 밀집 개선판은 광고 0.8초를 유지하며, 등산로/도심은 기존 1.6초 광고를 사용한다. 다른 정책은 기본 주기로 선택 알고리즘만 비교한다. 같은 단순 스케줄의 threshold/LUT가 통합 정책의 복잡도 실익을 판단하는 중요한 비교다.

광고에서 수신한 메타데이터만 이웃 캐시에 넣는다. 이웃 보고의 배터리·GNSS 품질·정보 연령, 수신 RSSI, RSSI 기반 링크 추정만 정책에 넘긴다. 내부 위치·링크 확률·미발견 이웃 상태는 주지 않는다. 후보가 없으면 기본 탐색으로 복귀한다. 제타는 순위 가중치에 0.1의 균일 탐색 혼합을 넣어 후보마다 최소 0.1/K 확률을 보장한다.

방송 프레임을 받으면 RF 비용은 이미 발생한 것이다. 데이터 채택은 사전에 고른 parent에 한정하며, 선택되지 않은 프레임의 RX 비용도 계산한다. 같은 패킷은 한 번만 채택/중계 갱신하며 광고 반복 횟수는 따로 집계한다. 데이터는 최신 세대 위주로 한 패킷만 보유한다. 이 단순 저장/스케줄 모형의 제약을 보고서에서 설명한다.

환경은 독립 NumPy 스트림으로 미리 생성하고, 채널 성공과 외부 간섭은 시드·시각·채널·송수신자 키에 따라 결정한다. 정책 난수 호출 횟수가 환경 난수열을 진행시키지 않는다. 정책마다 광고 시각이 달라져 경험하는 채널 표본이 다른 것은 행동의 결과다. 모든 정책의 환경 fingerprint 일치를 보고서 생성 때 검증한다.

## 패킷·단위·검증

논리 패킷은 `version=1`, `packet_id=source:sequence`, `source_id`, `message_type=virtual_gnss`, `created_at/expires_at` [시뮬레이터 초], `hop_count/max_hops`, `quality_code` [0..255], `payload_bytes` [0..8], `integrity_tag`를 정의한다. 시간은 부동소수 초이며 실제 펌웨어의 정수 밀리초 인코딩·wrap-around는 미구현이다. ID·hop·quality·길이는 정수 타입을 검사한다. 생성 이전·만료 시각 이후·잘못된 버전/필드/체크섬은 무시한다. 정확히 만료 시각에는 무효다. 체크섬은 인증이 아니다.

입력 특징은 결측 기본값·clipping 후 [-1,1]로 정규화한다. 체비쇼프는 품질 회귀 함수이며 `T3(x)=4x³−3x` 양자화 코덱과 무관하다. 1차 가산 성분에 15개 쌍별 상호작용을 더하고 Clenshaw로 평가한다. 합성 품질 목표 학습이라는 한계를 명시한다.

## 지표·에너지 해석

1차 지표는 50노드 전체 에너지 합계 J다. Donor/Relay/Seeker 비용과 TX/RX/scan/idle/sleep/CPU/GNSS 비용을 모두 별도 제공한다. 무선 상태 시간 합은 실행 시간과 일치하며 CPU는 증분 전력, GNSS는 별도 모듈이다. 전압·전류·MCU CPU 비용은 모두 **미실측 가정**이다. 표의 J를 보드 측정치로 표현하지 않는다.

성공률은 deadline 내 수명·최대 연령을 만족한 가상 패킷 수신 비율이다. 요청 시작 시 유효한 캐시가 있으면 0초 성공이다. p95 지연은 성공한 요청을 조건으로 하므로 실패율 및 실패에 deadline을 부여한 지연도 함께 본다. seed별 p95의 평균은 모든 패킷을 합친 p95와 다르다. summary/paired CSV의 n과 95% CI를 확인한다.

모든 실행은 `manifest.json`에 명령·설정 전문·실제 환경·시드·코드 버전·전체 벽시계 시간을, `runs.csv`에 seed별 벽시계 시간·이벤트 수·20ms 표본 RSS 최댓값을 기록한다. `nodes.csv`와 `requests.csv`가 분해 원자료다. `source_snapshot.zip`은 실행 당시 코드이며, 소스 SHA256은 코드/config/모델/고정 의존성을 포함한다. 체크섬 캐시 최적화 전 튜닝 스냅샷도 보존했다. 최적화 전후 dense seed=200 fixed/cheb_only/combined의 모든 시뮬레이션 수치가 일치함을 확인했다.

## 미실행·재개

실물 접근 부재로 ESP32-C3 3대 측정, Windows 5600X의 4/6프로세스 측정, GNSS 수신기 주입, MCU Flash/RAM·추론 에너지 검증은 수행하지 않았다. RL teacher와 증류는 이번 초기 단계 뒤의 작업이다. 미검증 항목을 시뮬레이션으로 대체해 실증했다고 쓰지 않는다. 펌웨어 절차는 `firmware/esp32c3/README_ko.md`를 참고한다.

중단된 실행은 `checkpoint_runs.csv`를 확인할 수 있다. 체크포인트에서 건너뛰기 재개는 구현하지 않았으며 같은 명령의 `--out`을 새 디렉터리로 바꿔 결정적으로 재실행한다. 실패를 예시 데이터로 채우지 않는다.
