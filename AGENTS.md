# ZetaMesh 버전 보존 규칙

새 개발을 시작하기 전에 versions/README_ko.md를 읽는다.
V2 태그 zetamesh-v2.0.0과 baseline/v2는 고정 기준점이다. 이동·삭제·강제 갱신하지 않는다.
V3 기능은 development/v3 브랜치와 별도 worktree에서 개발한다. main 또는 V2 APK를 직접 덮어쓰지 않는다.
V3 앱은 org.zetamesh.gnss.v3 패키지로 V2와 분리하고 별도 APK 파일을 사용한다.
사용자 업로드 원자료·개발 서명키·실물 captures·개인 백업 ZIP은 공개 저장소에 커밋하지 않는다.
실패와 복귀는 기록을 보존하는 방식으로 수행한다. 검증 없이 가속·안전·실물 성공을 주장하지 않는다.
