# ZetaMesh 연구환경 설계서 — Ryzen 5 5600X / RAM 32 GB / GTX 960 / Windows

작성일: 2026-11-08

## 0. 판단

- **신규 PC·GPU 구매 없이 시작**한다.
- 핵심 병목은 대형 신경망 학습이 아니라 **BLE 광고/스캔/충돌/중계 이벤트를 얼마나 충실하고 효율적으로 모델링하느냐**이다.
- GTX 960은 compute capability 5.2 (Maxwell). CUDA 13 이상에서 Maxwell 지원이 제거되었으므로 **최신 GPU 학습을 전제로 설계하지 않는다**.
- 1단계는 Windows 네이티브 CPU Python, 2단계 선택적으로 WSL2/Linux, ESP32 펌웨어 개발은 Windows VS Code + ESP-IDF를 권장한다.

## 1. 권장 아키텍처

```text
Windows (호스트)
 ├─ VS Code + Git
 ├─ Python 3.11 x64 / venv / CPU 기반 연구환경
 │    ├─ NumPy / SciPy / SimPy       : 이벤트·수치 시뮬레이션
 │    ├─ pandas / matplotlib        : 결과 분석
 │    ├─ scikit-learn / Optuna      : 품질 점수·계수 최적화
 │    ├─ PyTorch CPU + Gymnasium + Stable-Baselines3 : 정책 학습
 │    └─ pytest / psutil / pyserial : 검증·성능 진단·시리얼 로그
 ├─ VS Code ESP-IDF 확장
 │    ├─ ESP32-C3 Donor
 │    ├─ ESP32-C3 Relay
 │    └─ ESP32-C3 Seeker
 └─ [선택] WSL2 Ubuntu
      └─ Linux 전용 시뮬레이션·도구가 필요할 때만 사용
```

**주의:** WSL2는 스마트폰에 Linux를 설치하는 것과 다르다. ESP32 USB 연결과 플래싱은 먼저 Windows 네이티브에서 한다.

## 2. Windows 네이티브 설치 (PowerShell)

### 2.1 준비
- Python 3.11 x64 설치 후 `py -3.11 --version`으로 확인.
- Git, Visual Studio Code 설치.
- 프로젝트 폴더 예시: `C:\ZetaMesh`.

```powershell
mkdir C:\ZetaMesh
cd C:\ZetaMesh
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install numpy scipy pandas matplotlib scikit-learn simpy gymnasium optuna pytest psutil pyserial jupyterlab
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install stable-baselines3 tensorboard
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__, 'GPU:', torch.cuda.is_available())"
```

- 위 설치는 CPU 학습을 기준으로 한다. `GPU: False`는 이 구성에서는 정상이다.
- Windows PowerShell 스크립트 실행 정책으로 활성화가 안 되면 `.venv\Scripts\python.exe`를 직접 사용한다.
- 호환성이 확인되면 `pip freeze > requirements-lock.txt`로 환경을 고정한다.

### 2.2 ESP32-C3 펌웨어 도구
- Windows 네이티브 VS Code에서 공식 **ESP-IDF** 확장을 설치한다.
- `ESP-IDF: Open ESP-IDF Installation Manager`를 이용해 설치한다.
- 기본 BLE 광고·스캔 -> 역할별 메시지 -> 중계 -> GNSS UART 연결 순서로 시험한다.
- 실제 Bluetooth Mesh 표준 사용과 사용자 정의 BLE 중계 프로토콜은 구분하여 테스트한다.

### 2.3 [선택] WSL2 설치
Windows 11, 또는 지원하는 Windows 10 환경에서 관리자 PowerShell:

```powershell
wsl --install -d Ubuntu-24.04
```

Windows 에디션/버전, 가상화 설정에 따라 설치 가능 여부가 다르다. 현재 작업은 **WSL2 없이도 시작 가능**하다.

## 3. 연구 작업별 연산 예산

| 작업 | 초기 범위(예시) | 주된 제약 | 권장 실행 |
|---|---|---|---|
| 체비쇼프 근사 및 회귀 | 수천~수십만 입력 | 수치오차·모델 일반화 | NumPy/SciPy CPU |
| 최적 노드 선택 | 3~100개 노드 | 신선도/링크/지연 정의 | scikit-learn/Optuna CPU |
| 단순 이웃 기하 모델 | 20, 100, 300, 1,000노드 | 공간 탐색·이동성 | SciPy cKDTree CPU |
| 상세한 이벤트 기반 BLE 모델 | 3~100노드부터 | 이벤트 빈도·중복/충돌 | SimPy CPU |
| 단일 Seeker 중심 PPO | 수만~수십만 단계부터 | 환경 step 속도 | SB3 `device="cpu"` |
| 다중 에이전트 강화학습 | 첫 단계 비추천 | 상태·행동 공간 폭증 | 공유 정책/중앙학습 이후 |

이 값은 **실제 벤치마크 결과가 아니라 시작할 실험 규모**이다. 물리 채널, 시간 해상도, 이벤트 설계가 달라지면 수용 가능한 노드 수도 크게 달라진다.

### CPU 자원 설정
- 병렬 시뮬레이션은 **4개 프로세스**로 시작하고, 6개와 비교한다.
- Windows·IDE와 동시 실행하므로 우선 RAM 사용 상한 20~24GB를 목표로 한다.
- 에피소드마다 불필요한 모든 패킷 이벤트를 RAM에 저장하지 않고 요약 통계·압축 로그를 남긴다.
- Monte Carlo는 독립 시드, 학습/검증 시나리오 분리, 반복 실행을 지킨다.

## 4. 3개 계층의 모델

### L0: 수학·정책 검증
- 근사 함수의 입력 도메인을 `[-1, 1]`로 정규화한다.
- 체비쇼프 계수는 학습 후 **ESP32에서 Horner/Clenshaw 방식으로 평가**한다.
- 다항식 차수 3, 5, 7, 9를 비교한다.
- 단순 if-else / LUT / 선형 회귀 / 결정트리와 CPU 시간·RAM·오차를 비교한다.

### L1: 경량 BLE 네트워크 시뮬레이션
- 상태: 노드 위치, 링크 성공 확률, 배터리, 광고 간격, 스캔 윈도우, 보조정보의 유효기간.
- 이벤트: 광고 시작, 광고 송신, 수신 가능 여부, 검색 성공, 메시지 중계, 데이터 만료, 배터리 에너지 누적.
- 명시적 한계: 채널·간섭을 단순화하면 실제 무선 실험을 대체하지 못한다.
- 모델 보정: ESP32에서 RSSI별 수신 성공률, 전류, 스캔 지연을 직접 측정해 반영한다.

### L2: 실장 시제품
- A=Donor, B=Relay, C=Seeker.
- A-C 직접 연결 실패 상태에서 A-B-C 중계 검증.
- 초기에는 가상 GNSS 보조 패킷을 쓰고, 실제 GNSS 모듈/보조정보 주입은 별도 단계에서 검증.
- 각 보드의 시리얼 로그를 PC에서 타임스탬프와 함께 수집한다.

## 5. 정책 상태·행동·보상

### 관측 상태(초기 8~12개 특징)
- 최근 수신 RSSI / 링크 성공률 / 주변 노드 수
- 본인 배터리 수준 / 움직임 유무 / 마지막 탐색 이후 경과시간
- Donor GNSS 품질 / 보조정보 연령 / 예상 중계 홉 수
- 새 메시지 요구 여부 / 이전 탐색 실패 횟수

### 행동(처음에는 이산화)
- 광고 간격: 느림/보통/빠름
- 스캔 듀티사이클: 낮음/중간/높음
- 다음 탐색 노드 선택: 최고 점수/확률 탐색/전환
- 중계: 허용/일시 중단 (정보 신선도·긴급 메시지에 안전 예외)

### 보상 함수(가중치는 실험적으로 보정)

\[
R = w_1 \cdot \mathrm{fresh\_delivery} - w_2\cdot E_{\mathrm{total}} - w_3\cdot \mathrm{delay} - w_4\cdot \mathrm{expired\_or\_lost}
\]

- 에너지는 mJ 또는 J, 지연은 s, 전달률은 0~1로 **단위와 범위를 먼저 정규화**해야 한다.
- 배터리 절감만 최대화하면 아무것도 수신하지 않는 정책이 생길 수 있으므로 전달 성공률·지연에 **최소 품질 제약**을 둔다.
- Donor 배터리 부담까지 포함한 **네트워크 전체 에너지**도 평가한다.

## 6. 반드시 비교할 기준선

1. 고정 광고·탐색 주기 (AI 미사용)
2. 의사난수 지연/백오프
3. 현재 GNSS 품질이 가장 좋은 Donor만 선택하는 그리디 정책
4. 제타형 순위 가중치 `P(r) ∝ r^{-s}`
5. 작은 결정트리/MLP 정책
6. 학습 정책을 체비쇼프 다항식으로 증류한 정책

체비쇼프는 **범용 압축 마법**이 아니며, 제타형 가중치가 항상 우월하다는 전제도 두지 않는다.

## 7. 평가 지표·시험 설계

- 발견 시간: 평균 및 p50/p90/p95.
- 성공률: 주어진 데드라인 내 유효 보조정보 수신율.
- 중계: 홉 수, 중복 송신 횟수, 데이터 만료율.
- 에너지: `E = integral(V * I dt)`로 측정. CPU/BLE/GNSS/절전·중계 비용 포함.
- 기준선 대비 절감률: `(E_baseline - E_candidate) / E_baseline * 100%`.
- 형평성: donor 에너지 증가를 숨기지 말고 합산·분리하여 보고.
- GNSS: TTFF와 위치 오차는 수신 모듈이 실제 A-GNSS 주입을 지원하는 경우에 한해 직접 검증.
- 3개 지형: 산악 희소, 도심 차폐, 밀집 군집.
- 시드와 입력 데이터 분리; 동등한 거리·출력·안테나·전원 조건에서 비교.
- 실험에 앞서 성공 기준을 고정하고 반복 결과의 신뢰구간을 보고한다.

## 8. 폴더 구조

```text
ZetaMesh/
 ├─ README.md
 ├─ requirements-lock.txt
 ├─ configs/                 # 시나리오 / 난수 시드 / 파라미터
 ├─ simulator/               # 이벤트 / 채널 / 노드 / 에너지
 ├─ policies/                # fixed / random / zeta / chebyshev / RL
 ├─ training/                # Gymnasium 환경 / 학습 / 체크포인트
 ├─ benchmarks/              # CPU 및 알고리즘별 성능
 ├─ evaluation/              # 평균/분위수/신뢰구간/그래프
 ├─ firmware/esp32c3/       # ESP-IDF 코드
 ├─ data/raw/                # 원본 시리얼/BLE 로그
 ├─ data/processed/          # 정제 데이터
 └─ reports/                 # 실험 보고서, 실패 기록
```

## 9. 첫 번째 실행 순서

1. 제공된 `capacity_probe.py`로 **본인 PC에서** 기하 모델과 다항식 계산 속도 측정.
2. 3노드 고정 정책 이벤트 시뮬레이터 작성; 고정 시드로 재현성 확보.
3. 20/100개 노드 시나리오로 확장하면서 평균 및 p95 발견 시간 측정.
4. 그리디와 제타형 선택 정책 비교; 초반에는 RL 없이 검증.
5. Gymnasium 환경 구성 후 작은 PPO 공유 정책 학습 (`device='cpu'`).
6. 학습 정책을 체비쇼프 다항식 또는 작은 LUT로 근사.
7. ESP32-C3 3대로 펌웨어 테스트, USB 시리얼 로그와 실제 전류 측정으로 모델 보정.
8. 개선이 재현되면 실제 GNSS 모듈과 보조정보 포맷 시험으로 확장.

## 10. 공식 참고 자료

- Microsoft WSL: https://developer.microsoft.com/en-us/windows/wsl
- NVIDIA Legacy CUDA GPUs: https://developer.nvidia.com/cuda/gpus/legacy
- NVIDIA CUDA 13 변경: https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/
- PyTorch CPU: https://pytorch.org/get-started/locally/
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- ESP-IDF VS Code: https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html
- 공식 ESP-BLE-MESH 예시: https://github.com/espressif/esp-idf/tree/master/examples/bluetooth/esp_ble_mesh
