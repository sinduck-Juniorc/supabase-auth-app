# 밀집 50노드 성공률 개선 검증

설정 변경: `{'slow_adv_s': [1.6, 0.8]}`. 제타 순위 선택·최소 탐색확률·체비쇼프 계수/차수/Clenshaw·중계·TTL·만료·데드라인·PHY는 변경하지 않았다. 같은 밀집 YAML을 모든 정책에 적용했다. threshold/LUT에도 같은 스케줄 설정을 제공한다.

## 설계와 실행

`plan.json`의 사전 선택 규칙으로 튜닝 300~309에서 6설정을 비교하고 `selection.json`에 동결했다. 이후 새 평가 2000~2029에서 8정책 240회와 수정 전 combined 30회를 실행했다. 이전 1000~1029 결과에 다시 맞추지 않았다. 모든 paired 비교에서 환경 fingerprint가 일치했다. 기존 기준선 fixed를 유지했다. CI는 독립 시드별 값/paired 차이에 대한 양측 Student-t 95% CI다. 요청을 독립 표본으로 간주하지 않았다.

실행 환경: Linux-6.18.57-x86_64-with-glibc2.41, AMD EPYC 9V74 80-Core Processor, 2프로세스. Windows 5600X 및 UNO R4 실측 결과가 아니다. 평가 벽시계 455.74초. 이벤트 수·실행별 RAM·시드·코드 해시는 각 runs.csv와 manifest.json에 있다.

## 50노드 평가 평균

| policy | success_rate | energy_j | latency_p95_s | donor_j | relay_j | seeker_j |
| --- | --- | --- | --- | --- | --- | --- |
| combined_original | 0.815 | 59.132 | 7.791 | 18.213 | 12.177 | 28.743 |
| fixed | 0.968 | 84.990 | 3.872 | 27.557 | 17.230 | 40.203 |
| random | 0.980 | 84.989 | 4.709 | 27.556 | 17.230 | 40.203 |
| greedy | 0.998 | 84.990 | 1.737 | 27.557 | 17.230 | 40.203 |
| zeta_only | 0.992 | 84.990 | 2.574 | 27.557 | 17.230 | 40.203 |
| cheb_only | 0.997 | 85.021 | 1.809 | 27.563 | 17.238 | 40.221 |
| combined | 0.984 | 48.270 | 3.881 | 18.247 | 8.937 | 21.087 |
| threshold | 0.995 | 46.823 | 2.900 | 18.244 | 8.557 | 20.021 |
| lut | 0.993 | 46.263 | 2.737 | 18.245 | 8.325 | 19.693 |

성공률 열은 0~1 비율이다. 수정 후 평균 성공률 98.38%, 95% CI [97.92, 98.85]%, 시드별 최저 95.04%, 90% 미만 시드 0/30.

## paired 차이와 초기 성공 조건

| baseline | metric | n | mean | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| original | success_delta_pp | 30 | 16.914 | 15.455 | 18.373 |
| original | energy_delta_j | 30 | -10.862 | -11.198 | -10.527 |
| original | energy_reduction_pct | 30 | 18.359 | 17.854 | 18.864 |
| original | latency_delta_s | 30 | -3.910 | -4.320 | -3.499 |
| original | latency_relative_increase_pct | 30 | -49.568 | -53.956 | -45.179 |
| fixed | success_delta_pp | 30 | 1.620 | -0.216 | 3.456 |
| fixed | energy_delta_j | 30 | -36.720 | -37.008 | -36.431 |
| fixed | energy_reduction_pct | 30 | 43.205 | 42.865 | 43.545 |
| fixed | latency_delta_s | 30 | 0.009 | -1.641 | 1.659 |
| fixed | latency_relative_increase_pct | 30 | 미정 | 미정 | 미정 |
| cheb_only | success_delta_pp | 30 | -1.291 | -1.771 | -0.812 |
| cheb_only | energy_delta_j | 30 | -36.751 | -37.039 | -36.462 |
| cheb_only | energy_reduction_pct | 30 | 43.226 | 42.886 | 43.566 |
| cheb_only | latency_delta_s | 30 | 2.072 | 1.610 | 2.534 |
| cheb_only | latency_relative_increase_pct | 30 | 242.536 | 108.600 | 376.471 |
| zeta_only | success_delta_pp | 30 | -0.834 | -1.392 | -0.277 |
| zeta_only | energy_delta_j | 30 | -36.720 | -37.008 | -36.432 |
| zeta_only | energy_reduction_pct | 30 | 43.205 | 42.865 | 43.545 |
| zeta_only | latency_delta_s | 30 | 1.307 | 0.777 | 1.837 |
| zeta_only | latency_relative_increase_pct | 30 | 169.783 | -0.062 | 339.627 |
| lut | success_delta_pp | 30 | -0.943 | -1.475 | -0.412 |
| lut | energy_delta_j | 30 | 2.007 | 1.660 | 2.355 |
| lut | energy_reduction_pct | 30 | -4.368 | -5.145 | -3.591 |
| lut | latency_delta_s | 30 | 1.145 | 0.701 | 1.588 |
| lut | latency_relative_increase_pct | 30 | 65.519 | 24.425 | 106.614 |
| threshold | success_delta_pp | 30 | -1.107 | -1.625 | -0.588 |
| threshold | energy_delta_j | 30 | 1.447 | 1.018 | 1.877 |
| threshold | energy_reduction_pct | 30 | -3.143 | -4.084 | -2.202 |
| threshold | latency_delta_s | 30 | 0.981 | 0.565 | 1.397 |
| threshold | latency_relative_increase_pct | 30 | 52.752 | 23.829 | 81.676 |

평균값 기준 원래 세 조건 동시 충족: False. CI와 개별 시드 변동을 함께 판단해야 하며 다른 토폴로지에서 90%를 보장하지 않는다. `lut`, `threshold`가 비슷하거나 우수하면 통합 정책의 추가 복잡도를 정당화하지 않는다.

## 원인과 한계

| policy | tx_j | rx_j | scan_j | idle_j | sleep_j | cpu_j | gnss_j |
| --- | --- | --- | --- | --- | --- | --- | --- |
| combined_original | 0.269 | 0.751 | 44.570 | 0.074 | 0.239 | 0.029 | 13.200 |
| combined | 0.375 | 0.772 | 33.552 | 0.088 | 0.252 | 0.031 | 13.200 |

이번 평가에서 단순 LUT/threshold의 평균 에너지·성공률·지연이 통합 정책보다 좋았다. 90% 목표 달성은 제타·체비쇼프의 우월성 증거가 아니며 추가 복잡도를 정당화하지 않는다. 핵심 아이디어 보존 요청에 따라 선택 알고리즘을 단순 정책으로 교체하지 않았다.

기준선 p95가 0이고 통합 p95가 양수이면 상대 악화율은 무한대로 기록하고 평균 성공 조건을 통과시키지 않는다. 둘 다 0이면 변화율은 0이다. 비유한 상대 변화율은 CI를 계산하지 않으며 표의 미정 표기와 CSV 원값을 함께 확인한다.

변경은 과도한 광고 절전을 완화해 신선한 패킷의 재공급 기회를 늘리는 것이다. 더 잦은 광고가 TX 비용을 늘리더라도, 신선한 패킷을 유지하면 긴 탐색 스캔으로 복귀하는 시간이 줄어 전체 에너지가 감소할 수 있다. 상태별 원자료로 확인해야 하며 추론 연산 비용 감소와 혼동하지 않는다. 에너지는 미실측 전류 가정값이다. p95는 성공한 요청의 지연이며 실패를 deadline으로 대체한 p95도 summary.csv에 보고했다. 등산로/도심 설정과 원래 보고서는 보존했다. 이번 범위는 밀집 설정 수정이며 다른 두 시나리오와 전류 민감도 실험은 재실행하지 않았다. R4 펌웨어의 실제 무선 성능 개선을 검증한 결과가 아니다.

## Windows 재현

프로젝트 루트에서 기존 고정 의존성을 설치한 뒤 실행한다. 새 출력 폴더를 사용한다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase evaluation --config configs/50nodes_dense.yaml --seed-start 2000 --seeds 30 --workers 4 --out outputs/dense90_replay
.\.venv\Scripts\python.exe -m scripts.run_experiment --phase evaluation --config revisions/dense90/configs/original.yaml --policy combined --seed-start 2000 --seeds 30 --workers 4 --out outputs/dense90_original_replay
```

`MPLCONFIGDIR`을 쓰기 가능한 경로로 설정하고 `python -m scripts.dense90_revision report`로 제공된 원자료의 보고서/그림을 재생성한다. 평가 후 freeze를 재실행하면 오류가 난다. 새 튜닝은 새 연구 디렉터리와 미사용 평가 시드로 진행한다.

## 다음 실물 검증

R4 한 대 광고/스캔 로그를 수집하고, 3노드를 확보하면 동일 광고 간격 비교에서 실제 수신률·보드 전류·기한 내 전달을 측정한다. GNSS 주입/TTFF는 별도 검증한다.
