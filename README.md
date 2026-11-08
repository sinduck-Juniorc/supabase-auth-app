# Supabase 인증 앱

`space-quiz`와 별도로 만든 Next.js 앱이다. Supabase 이메일·비밀번호 로그인/회원가입, 확인 메일, 서버에서 검증하는 보호 경로를 제공한다. GitHub는 소스 관리 대상으로 사용하며 GitHub OAuth 로그인은 이번 범위에 포함하지 않는다.

## 연결된 프로젝트

- 이름: `supabase-auth-app`
- Supabase 참조: `bonejjsjfagjpdbxqwyz`
- 리전: 서울 (`ap-northeast-2`)
- 프로젝트 주소: `https://bonejjsjfagjpdbxqwyz.supabase.co`
- 관리 화면: https://supabase.com/dashboard/project/bonejjsjfagjpdbxqwyz
- 선택한 개인 조직의 생성 시 조회 비용: 월 $0, Free 플랜. 추후 요금제·사용량 변경은 해당 계정 설정에 따른다.

## 실행

Node.js 22.14 이상과 npm이 필요하다. 구현/검증 환경은 Node.js 24.22.1과 Linux다. 경로 처리는 Windows에서도 동작하도록 구성했다.

PowerShell:

```powershell
npm ci
Copy-Item .env.example .env.local
# .env.local에 Supabase 프로젝트의 publishable 키를 입력한다.
npm run dev
```

macOS/Linux:

```bash
npm ci
cp .env.example .env.local
# .env.local의 SUPABASE_PUBLISHABLE_KEY를 설정한다.
npm run dev
```

브라우저에서 `http://localhost:3000`을 연다. 현재 클라우드 작업 폴더에는 실제 프로젝트의 publishable 키가 들어 있는 `.env.local`을 구성했다. 이 파일은 Git 추적에서 제외한다. 키는 Supabase 관리 화면의 **Settings → API Keys**에서 확인할 수 있다. `service_role` 또는 `sb_secret_...` 키는 사용하지 않는다.

| 설정 | 내용 |
|---|---|
| `SUPABASE_URL` | Supabase 프로젝트 API 주소 |
| `SUPABASE_PUBLISHABLE_KEY` | 해당 프로젝트의 활성 publishable 키 |
| `APP_URL` | 앱의 신뢰할 수 있는 기본 주소. 로컬은 `http://localhost:3000`, 배포는 HTTPS |

API URL/키는 이 앱의 서버에서 사용한다. 브라우저 Supabase 클라이언트를 별도로 만들지 않아 세션 쿠키를 HttpOnly로 유지한다. 앱 UI는 서버 액션과 서버 렌더링을 사용한다.

## 경로

| 경로 | 접근 및 기능 |
|---|---|
| `/` | 공개 홈 |
| `/login` | 이메일·비밀번호 로그인 |
| `/signup` | 회원가입과 확인 메일 요청 |
| `/auth/callback` | PKCE 확인 코드 교환 |
| `/auth/confirm` | 별도 확인 메일 템플릿의 email/signup 토큰 검증 |
| `/dashboard` | 로그인한 사용자의 공간. 비로그인은 로그인 화면으로 이동 |
| `/account` | 검증된 본인 계정 정보. 비로그인은 로그인 화면으로 이동 |
| `/api/private` | 검증된 사용자에게만 JSON 반환. 비로그인은 HTTP 401 |

로그아웃은 POST 서버 액션이다. 로그인 후 이동 가능한 경로는 `/dashboard`, `/account`로 제한한다. 로그인 실패 사유로 계정 존재 여부를 구분해 노출하지 않는다. 비밀번호 최소 12자·최대 128자와 확인 입력을 서버에서도 검사한다.

## 이메일 확인과 배포 설정

연결된 원격 프로젝트에서 이메일 인증 활성화와 이메일 확인 필수 설정을 조회했다. 원격 테스트에서는 외부 확인 메일을 발송하지 않았다.

Supabase의 **Authentication → URL Configuration**에서 앱이 실제 사용하는 기본 주소와 리다이렉트 주소를 확인한다. 로컬 주소와 배포 주소가 다르면 각각 정확히 등록해야 한다.

- 로컬 Site URL: `http://localhost:3000`
- 로컬 Redirect URL: `http://localhost:3000/auth/callback`
- 배포 후 `APP_URL`과 Site URL: 실제 HTTPS 앱 주소
- 배포 Redirect URL: `https://실제-앱-주소/auth/callback`

이 연결 도구에는 Auth URL 설정을 변경하는 API가 없어, 관리 화면의 리다이렉트 허용 목록 변경은 자동으로 수행하지 않았다. 기본 확인 메일의 링크가 `/auth/callback`으로 돌아오도록 등록한다. 커스텀 확인 메일 템플릿을 사용한다면 다음 형태의 토큰 해시 경로도 지원한다.

```html
<a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&next=/dashboard">이메일 확인</a>
```

배포 플랫폼에는 세 환경 변수를 서버 환경 변수로 설정한다. 사용자 응답과 Set-Cookie 응답을 CDN/공유 캐시에 저장하지 않는다. 이 작업에서는 호스팅 서비스에 앱을 배포하지 않았다.

## 보호 방식

- `src/proxy.ts`가 매 요청에서 `auth.getUser()`로 Auth 서버의 검증을 거쳐 쿠키를 갱신한다.
- 보호 페이지와 API도 `src/lib/auth.ts`를 통해 각각 검증한다. 레이아웃이나 브라우저 표시만으로 보호하지 않는다.
- `getSession()`의 사용자 객체, 클라이언트 상태, 사용자 수정 가능 메타데이터를 권한 판단에 사용하지 않는다.
- 쿠키는 HttpOnly·SameSite=Lax이며 HTTPS 환경에서는 Secure를 사용한다. 응답에 `private, no-store`를 설정한다.
- `APP_URL`은 설정값에서만 읽고 전달된 Host/리다이렉트 매개변수를 신뢰하지 않는다.
- 현재 앱에는 공개 데이터 테이블·관리자 권한·저장소 업로드 기능이 없다. 기능을 추가할 때는 보호 API 외에도 RLS와 소유권 조건을 정의해야 한다.
- JWT가 발급된 뒤의 세션 폐기·사용자 삭제를 즉시 반영하는 엄격한 권한 모델은 별도 요구사항이다. 민감한 작업을 추가하면 세션 검증 정책을 함께 설계한다.

## 검사

```bash
npm test
npm run typecheck
npm run build
npm run verify:remote
```

`verify:remote`는 실제 Supabase의 공개 Auth 설정을 조회하고 잘못된 JWT가 거부되는지 검사한다. 클라우드처럼 프록시가 필요한 환경에서는 제공된 프록시·CA를 유지하고 Node의 `NODE_USE_ENV_PROXY=1`을 사용한다.

브라우저 통합 시험은 Docker가 필요하다. PostgreSQL·실제 GoTrue·Mailpit를 로컬에서 실행해 외부 메일 없이 가입/메일 확인/로그인/계정/로그아웃을 검증한다. 이 서비스는 실제 원격 프로젝트의 데이터베이스와 분리되어 있다. Compose의 비밀번호와 JWT 문자열은 이 폐기 가능한 시험용 서비스에서만 사용한다.

```bash
npx playwright install chromium
npm run test:integration
```

Linux에 `/usr/bin/chromium`이 있으면 이를 사용하며 다른 환경은 Playwright Chromium을 사용한다. 시험 후 해당 Compose 프로젝트만 정리한다. 테스트는 보호 경로·위조 쿠키 거부·확인 링크·로그아웃 후 차단·로그인 후 목적지 복구·세션 갱신·모바일 화면을 다룬다.

## GitHub

소스 저장소: https://github.com/sinduck-Juniorc/supabase-auth-app

사용자가 생성한 공개 저장소를 사용한다. 기존 `space-quiz` 저장소에는 변경을 쓰지 않았다. `.env.local`, `node_modules`, `.next`는 Git 추적에서 제외한다.

```bash
git clone https://github.com/sinduck-Juniorc/supabase-auth-app.git
cd supabase-auth-app
npm ci
```

이후 위 실행 안내에 따라 `.env.local`을 구성한다. `.github/workflows/verify.yml`은 단위 검사·타입 검사·프로덕션 빌드 및 로컬 Auth 통합 시험을 실행한다. 원격 검사 결과는 https://github.com/sinduck-Juniorc/supabase-auth-app/actions 에서 확인한다.

## 주요 파일

`src/lib/supabase/server.ts`, `src/lib/auth.ts`, `src/proxy.ts`, `src/app/auth/actions.ts`, `src/app/auth/{callback,confirm}/route.ts`, `src/app/{login,signup,dashboard,account}/page.tsx`, `src/app/api/private/route.ts`, `tests/`.

공식 참고: https://supabase.com/docs/guides/auth/server-side/creating-a-client 및 https://supabase.com/docs/guides/auth/passwords
