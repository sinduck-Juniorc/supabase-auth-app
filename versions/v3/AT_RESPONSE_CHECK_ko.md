# 기본 AT 한 번 확인 — Windows CMD

## 범위와 현재 상태

`tools/at_probe.py`는 기본 `AT` 응답 확인용이다. Windows/삼성 드라이버 실측은 아직 하지 않았다. 모의 시험 통과는 통신 성공이 아니다. 클라우드는 사용자 PC의 COM3를 직접 열 수 없으므로 아래 실물 단계는 사용자 PC에서 실행한다. 기존 USB 설정·INF·ADB 도움말 전체를 다시 수집할 필요는 없다.

## 고정 실행 조건

| 항목 | 값 |
| --- | --- |
| 포트 | COM3 기본값, `--port COM번호`로 명시 |
| 전송률 / 프레임 | 115200 baud / 8 data bits, parity None, 1 stop bit |
| 흐름 제어 | XON/XOFF, RTS/CTS, DSR/DTR 모두 비활성 |
| 제어선 | 열기 전에 DTR=False, RTS=False 요청 |
| 송신 | `AT\r` (`41 54 0d`) 한 번, 재시도 없음 |
| 쓰기 제한 | 1초, 부분 전송도 재전송하지 않음 |
| 읽기 제한 | 한 번 읽기 0.1초, 전송 후 관찰 3초, 최대 4096바이트 |
| 종료 | 성공·시간 초과·예외·Ctrl+C 시 finally에서 close 시도 |

115200과 DTR/RTS 값은 이번 최초 시험 조건이며 INF로 입증된 단말 필수값이 아니다. OS/드라이버가 open 시 제어선을 순간 변경하거나 요청을 다르게 처리할 수 있다. 열기·닫기는 무조건 무변경 작업이 아니다. OS의 open/close 호출 자체와 강제 프로세스 종료에는 위 응답 시간 제한·정상 close가 보장되지 않는다. 멈추면 연속 실행하지 말고 상태를 확인한다.

열린 직후 기존 수신 버퍼를 비우고 전송한다. 초기화(ATE0 등), 리셋(AT&F), 다이얼, 식별자/위치 질의는 보내지 않는다. `flush()`로 무기한 배출 대기를 하지 않는다. 완전한 줄의 `OK` 또는 `ERROR`만 판정하며 에코·부분 문자열은 성공으로 간주하지 않는다. URC나 지연 응답과의 완벽한 인과 구분은 불가능하므로 다른 포트 프로그램은 종료한 상태에서 시험한다.

## 한 줄씩 실행

저장소가 PC에 있는 경우 `development/v3` 최신 내용을 받은 저장소 루트 CMD에서 실행한다. 로컬 변경이 있으면 덮어쓰지 않는다. 저장소가 없는 PC는 GitHub의 이 파일과 `versions/v3/tools/at_probe.py`를 받아 검토한 뒤 스크립트가 있는 폴더에서 파일 이름만 `at_probe.py`로 바꿔 실행할 수 있다. ADB는 필요 없다.

먼저 계획만 출력한다. 이 명령은 pyserial 설치 없이도 실행되며 포트를 열지 않는다.

```cmd
python versions\v3\tools\at_probe.py --plan
```

`python`이 없고 `py` 실행기가 있다면 아래를 포함해 모든 `python`을 `py -3`으로 일관되게 바꾼다. 둘 다 없다면 설치 상태를 먼저 확인한다.

실제 전송에 필요한 의존성은 동일 Python 환경에 설치한다.

```cmd
python -m pip install pyserial==3.5
```

COM3가 여전히 삼성 모뎀 포트인지 확인하고 다른 직렬 터미널을 종료한다. 계획에 적힌 조건으로 한 번만 실행한다.

```cmd
python versions\v3\tools\at_probe.py --send-at --port COM3
```

명령이 종료되면 출력된 `result` 요약만 공유한다. 포트 번호가 달라졌다면 실제 번호를 지정하며 번호·baud·제어선을 자동 탐색하지 않는다. 결과 JSON은 현재 폴더 기준 `captures/v3/at-시간.json`에 독점 생성하고 기존 파일을 덮어쓰지 않는다. 원문 수신·개인 식별자·OS 오류 원문은 저장하지 않는다. 저장소 안의 `captures/`는 Git 제외이며, 별도로 다운로드해 실행한 폴더의 결과도 공개 저장소에 올리지 않는다.

## 결과에 따른 다음 단계

- `status=ok`, `terminal_response=OK`, `closed=true`: 이번 조건에서 기본 AT 응답 관찰. 위치 주입·기지국 탐색 제어 성공을 뜻하지 않는다. 다른 AT 명령은 자동 실행하지 않고 결과를 먼저 기록한다.
- `error_response`: ERROR 응답 관찰. 기본 AT 성공은 아니며 원인 검토 후 다음 단계를 결정한다.
- `timeout`: 제한 시간 내 완전한 OK/ERROR 없음. `bytes_received`로 무응답과 기타 응답을 구분하되 AT 미지원으로 단정하지 않는다.
- `partial_write`, `io_error`, `receive_limit`, `close_error`: 중지하고 요약을 검토한다. open 실패면 다른 프로그램 점유·포트 변경·연결 상태를 우선 확인한다. 자동 재시도·관리자 실행·드라이버 변경은 하지 않는다.

종료 코드 0은 정상 close를 포함한 OK 관찰, 2는 비성공/CLI 조건 오류다. 결과 파일 생성 자체가 실패하면 포트를 열지 않으며 Python 파일 오류가 출력될 수 있다. 강제 종료 시 빈/미완성 파일이 남을 수 있으므로 이를 성공 증거로 사용하지 않는다.

클라우드 검증 명령: `python -m unittest discover -s versions/v3/tests -v`. 이 시험은 모의 포트만 사용한다.
