# S26+ 기지국 탐색 개선 검토

현재 일반 앱 방식의 MVP는 폐기를 권고한다. ADB·통신사·OEM 경로를 포함한 모든 우회가 없다고 증명한 것은 아니다. S26+ 성능은 미측정이다. 기존 Fold3 코드는 보존했다.

- [10쪽 보고서 PDF](REPORT_ko.pdf), [HTML](REPORT_ko.html), [원고](REPORT_ko.md)
- [논리 검토 및 미확인 사항](REVIEW_ko.md)
- [근거 목록](SOURCES.md), [AOSP 발췌](evidence/AOSP_EXCERPTS.md)
- [읽기 전용 진단 도구](tools/probe.py), [검증 기록](verification/)

## Windows 재개 명령

Python 3.11 x64와 Android Platform Tools를 사용한다. USB 디버깅을 허용한 자신의 휴대폰을 연결하고 저장소 루트에서 실행한다. `adb.exe`가 PATH에 없으면 `--adb`에 전체 경로를 지정한다.

```powershell
py -3.11 reports/s26-cell-search/tools/probe.py --plan
adb devices
py -3.11 reports/s26-cell-search/tools/probe.py --adb adb.exe --serial 기기번호 --out s26-capabilities.json
```

출력 파일이 있으면 덮어쓰지 않는다. 명령 오류는 종료 코드 2로 반환한다. 모든 명령이 반환되어도 권한 기록 누락은 null이며 실제 API 사용·GNSS 주입·성능 개선을 증명하지 않는다. JSON은 로컬 저장이며 자동 업로드하지 않는다. 개인 기기의 진단 파일을 공개 GitHub에 커밋하지 않는다.

## 수행한 검증과 미실행 항목

읽기 명령 계획 출력과 합성 입력 시험 5개를 실행했다. 기기가 연결되지 않아 S26+ 진단·설치·주입·네트워크 스캔·성능 비교는 실행하지 않았다. Linux 클라우드에서 수행한 코드 시험은 Windows PC나 S26+ 측정이 아니다. 새 가속 APK는 만들지 않았다.

```text
python3 -m unittest discover -s reports/s26-cell-search/tests -v
python3 reports/s26-cell-search/tools/render_report.py
node reports/s26-cell-search/tools/render_pdf.mjs
pdfinfo reports/s26-cell-search/REPORT_ko.pdf
```

진단 도구는 외부 Python 의존성이 없다. PDF 재생성은 저장소 lockfile의 Playwright와 Chromium, 한국어 폰트를 사용한다. `CHROMIUM_PATH`로 브라우저 경로를 지정할 수 있다. 렌더링 환경은 verification에 남긴다. 보고서 동결 후 검토는 저장된 근거로만 진행하며 새 웹 조사를 하지 않는다.
