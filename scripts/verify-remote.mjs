import assert from "node:assert/strict";

const base = process.env.SUPABASE_URL;
const key = process.env.SUPABASE_PUBLISHABLE_KEY;
assert(base && key, ".env.local의 Supabase 설정이 필요합니다.");
const settingsResponse = await fetch(base + "/auth/v1/settings", { headers: { apikey: key } });
assert(settingsResponse.ok, `Auth 설정 조회 실패: ${settingsResponse.status}`);
const settings = await settingsResponse.json();
assert.equal(settings.external.email, true);
const denied = await fetch(base + "/auth/v1/user", { headers: { apikey: key, Authorization: "Bearer invalid-token" } });
const failure = await denied.json();
assert([401, 403].includes(denied.status) && failure.error_code === "bad_jwt", "Auth 서버의 JWT 검증 거부 응답이 필요합니다.");
console.log(JSON.stringify({ projectUrl: base, emailAuthEnabled: settings.external.email,
  emailAutoConfirm: settings.mailer_autoconfirm, invalidTokenStatus: denied.status,
  verification: "원격 프로젝트에서 설정 조회와 잘못된 토큰 거부를 확인; 외부 이메일 발송 없음" }, null, 2));
