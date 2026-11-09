# ZetaMesh GNSS 지원 경로 진단

현재 배포판은 **0.1.1**이다. [안전성 보강 내역](CHANGES_0.1.1_ko.md)을 확인한다. S26+ Android 17 / One UI 9는 실기기 미검증이다.

[한국어 조사·적용 보고서](REPORT_ko.md)를 먼저 읽는다. 이 앱은 실제 GNSS 보조정보 갱신 요청과 TTFF 기록용이며, Fold3 가속 효과나 R4 좌표의 칩 주입을 입증한 제품이 아니다.

[설치 APK](downloads/ZetaMesh-GNSS-Assist-debug.apk) · [PDF 보고서](REPORT_ko.pdf) · [HTML 보고서](REPORT_ko.html) · [빌드 검증](verification/build.json)

대상 가정은 Fold3 공식 Android 15 / One UI 7.0, 최소 Android 11이다. 정확한 위치 권한을 허용하고 A/B/C 모드를 시험한 뒤 실제 로그를 내보낸다. 좌표는 저장하지 않고 자동 업로드도 하지 않는다. Supabase 계정은 이 진단 단계에서 필요하지 않다.

## 재현 빌드

Python 3.11, JDK 17 이상, Android SDK Platform 35와 Build Tools 35.0.0이 필요하다. Java SDK API로 작성한 최소 네이티브 앱으로 Gradle 다운로드 없이 SDK 도구로 빌드한다. Windows의 SDK 경로는 Android Studio SDK Manager에서 확인한다.

```powershell
py -3.11 tools\build.py --sdk "$env:LOCALAPPDATA\Android\Sdk" --keystore .local\dev.keystore
py -3.11 -m unittest discover -s tests -p "test_*.py" -v
```

리눅스의 실제 빌드 명령:

```bash
python tools/build.py --sdk /workspace/work/gnss-tools/sdk --keystore /workspace/work/gnss-tools/dev.keystore
```

빌드 스크립트는 Java 상태 검사, DEX 변환, manifest 링크, zipalign, 개발 서명과 서명 검사를 실행한다. 호스트 Java 검사와 APK 생성은 실제 Android UI/위성 수신 시험을 대신하지 않는다. Android 11 호환을 위해 사용한 일부 API의 deprecation 경고는 로그에 남아 있다.

## 실제 로그 분석

```powershell
py -3.11 tools\analyze.py 실제로그.jsonl --out 분석결과
```

종료가 없는 시험·실패·timeout도 분모에 남긴다. 원자료가 없으면 성공률이나 TTFF를 생성하지 않는다. 기기에서 실행한 JSONL 파일이 있어야 한다. 테스트의 합성 입력은 소프트웨어 검사 전용이다.
