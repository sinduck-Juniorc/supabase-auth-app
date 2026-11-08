import assert from "node:assert/strict";
import { test } from "node:test";
import { safeNext, isProtectedPath, loginPath, readCredentials } from "../src/lib/auth-paths";

test("로그인 후 목적지는 허용한 앱 경로로 제한한다", () => {
  for (const value of [undefined, null, "https://evil.test", "//evil.test", "/\\evil.test", "/%2f%2fevil.test", "/dashboard/../evil", "/auth/callback", "/api/private", ["/account"], "/account?next=https://evil.test"]) {
    assert.equal(safeNext(value), "/dashboard");
  }
  assert.equal(safeNext("/account"), "/account");
  assert.equal(safeNext("/dashboard"), "/dashboard");
});

test("보호 경로는 루트와 하위 경로까지 포함한다", () => {
  for (const path of ["/dashboard", "/dashboard/a", "/account", "/account/a", "/api/private", "/api/private/a"]) assert.ok(isProtectedPath(path));
  for (const path of ["/", "/login", "/signup", "/auth/callback", "/dashboard-public", "/accounting", "/api/private-public"]) assert.ok(!isProtectedPath(path));
  assert.equal(loginPath("/account"), "/login?next=%2Faccount");
});

function credentials(password = "test-password-12345") {
  const data = new FormData();
  data.set("email", "  person@example.test  "); data.set("password", password); data.set("confirmPassword", password);
  return data;
}

test("가입 입력은 이메일과 비밀번호 일치를 서버에서 검사한다", () => {
  assert.deepEqual(readCredentials(credentials(), true), { email: "person@example.test", password: "test-password-12345" });
  assert.equal(readCredentials(credentials("short"), true), null);
  assert.equal(readCredentials(credentials("x".repeat(129)), true), null);
  const data = credentials(); data.set("confirmPassword", "different-password");
  assert.equal(readCredentials(data, true), null);
  data.set("email", "invalid"); assert.equal(readCredentials(data), null);
  assert.equal(readCredentials(new FormData()), null);
});
