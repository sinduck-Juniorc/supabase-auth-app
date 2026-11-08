# 구현 및 검증 기록

새 앱 소스 경로: `supabase-auth-app`. 기존 `space-quiz`에는 쓰기 작업을 수행하지 않았다.

## 수행한 검사

| 항목 | 결과 | 증거 |
|---|---|---|
| 단위 검사 | 3개 통과 | `docs/verification/unit-tests.txt` |
| TypeScript 검사 | 통과 | `docs/verification/typecheck.txt` |
| Next.js 프로덕션 빌드 | 통과 | `docs/verification/integration.txt` |
| Chromium 통합 검사 | 5개 통과 | `docs/verification/integration.txt` |
| 원격 Supabase Auth | 이메일 활성화·확인 필수·잘못된 JWT HTTP 403 거부 확인 | `docs/verification/remote-auth.txt` |
| 원격 DB 확인 | `auth.users` 존재, 사용자 0명 | 읽기 전용 SQL 조회 |
| Supabase 보안 검사 | 알림 0개 | 연결된 프로젝트의 security advisor 조회 |
| 운영 의존성 감사 | 알려진 취약점 0개 | `docs/verification/dependency-audit.json` |

이 문서의 로컬 검증 환경은 Linux, Node.js 24.22.1, Docker 29.9.2, 시스템 Chromium이다. Windows에서의 직접 실행은 하지 않았다. GitHub Actions의 원격 실행 결과는 저장소의 Actions 기록에서 확인한다.

## 통합 시험 범위

- 비로그인 사용자의 `/dashboard`, `/account` 이동 차단 및 `/api/private` HTTP 401.
- 위조한 세션 쿠키 거부.
- 실제 로컬 GoTrue·PostgreSQL·Mailpit를 통한 회원가입과 확인 메일 링크 교환.
- HttpOnly·SameSite=Lax 쿠키, 본인 계정/보호 API, 로그아웃 후 차단.
- 틀린 비밀번호 오류 뒤 이메일 유지, 올바른 로그인과 원래 목적지 복구.
- 저장된 세션을 만료로 표시했을 때 실제 refresh token 교환과 갱신 쿠키.
- 외부 리다이렉트와 잘못된 확인 링크 처리.
- 모바일 로그인 화면과 가로 넘침 검사.

원격 프로젝트에 시험 계정을 만들거나 외부 확인 메일을 보내지 않았다. 로컬 테스트 서비스는 검사 뒤 정리했다. 화면 증거는 `docs/verification/home.png`, `docs/verification/login-mobile.png`다.

## 수정한 문제

React 서버 액션 오류 뒤 자동 폼 초기화로 이메일까지 지워지던 문제를 수정했다. 이메일은 유지하고 비밀번호는 다시 입력하도록 했으며, 해당 흐름을 브라우저 검사에 포함했다. 로컬 GoTrue 시험 DB의 스키마/검색 경로, 컨테이너 상태 검사, 메일 확인 URL도 검증 과정에서 보정했다.

## GitHub 연결 및 배포 범위

초기 GitHub 새 저장소 생성 요청은 `Resource not accessible by integration (createRepository)`로 거부됐다. 이후 사용자가 `sinduck-Juniorc/supabase-auth-app`을 생성했고 연결된 계정의 접근 권한을 확인했다. 저장소 주소는 https://github.com/sinduck-Juniorc/supabase-auth-app 이다. 초기 구현 커밋은 `7ceab12`이며 Git 기록에 보존한다.

앱 호스팅 배포와 원격 Auth 리다이렉트 허용 목록 변경은 수행하지 않았다. 배포 전에 실제 서비스 주소를 등록해야 한다. 구체적인 설정은 README에 있다.
