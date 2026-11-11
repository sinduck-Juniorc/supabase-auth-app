# Windows PC 프로젝트 파일 복원

Git 설치 없이 PowerShell과 인터넷으로 세 브랜치의 소스 스냅샷을 복원한다. 기준은 2026-11-11 확인한 refs이며 커밋·ZIP SHA-256은 tools/Restore-ZetaMesh.ps1에 고정했다. 브랜치가 나중에 이동해도 같은 내용을 받는다.

- C:\ZetaMesh\main
- C:\ZetaMesh\baseline\v2
- C:\ZetaMesh\development\v3

기존 목적지 폴더가 있으면 빈 폴더여도 중단한다. 기존 파일을 지우거나 덮어쓰지 않는다. 세 ZIP의 다운로드·해시·압축 구조를 검증한 뒤 각 폴더로 옮긴다. 중간 실패 시 .restore-임의문자 폴더와 이미 복원된 목적지에 결과가 남을 수 있다. 실패 후 기존 목적지를 임의 삭제하지 말고 오류를 확인한다.

이 결과는 .git 이력이 없는 소스 스냅샷이며 Git clone 저장소는 아니다. APK와 기존 추적된 보고서·시험 자료는 포함하지만 .env.local, 사용자 개인 로그, 개발 서명키, Supabase 데이터베이스, node_modules, Android SDK 등은 포함되지 않는다. 별도 Git 개발 설정과 환경 구성은 후속 단계다. GitHub에 없는 개인 파일을 복원 완료로 표시하지 않는다.

실행: PowerShell에서 powershell -NoProfile -ExecutionPolicy Bypass -File 다운로드한스크립트경로 를 사용한다. Bypass는 해당 프로세스의 스크립트 실행에만 적용되며 시스템 정책을 영구 변경하지 않는다. 대상 폴더는 -Root 인자로 바꿀 수 있다.

검증: 클라우드에서 세 고정 ZIP을 실제 다운로드해 ZIP 무결성과 package.json을 확인했고 해시를 고정했다. Windows PowerShell 실행과 사용자 C 드라이브의 최종 생성은 아직 확인하지 못했다.
