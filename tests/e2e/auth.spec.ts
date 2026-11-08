import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

const password = "Local-only-test-password-123!";
async function register(page: Page, request: APIRequestContext) {
  const email = `test-${Date.now()}-${Math.random().toString(16).slice(2)}@example.test`;
  await page.goto("/signup");
  await page.getByLabel("이메일", { exact: true }).fill(email);
  await page.getByLabel("비밀번호", { exact: true }).fill(password);
  await page.getByLabel("비밀번호 확인", { exact: true }).fill(password);
  await page.getByRole("button", { name: "계정 만들기", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("이메일의 확인 링크");
  await expect.poll(async () => {
    const res = await request.get("http://127.0.0.1:58025/api/v1/messages");
    const data = await res.json();
    return data.messages.find((message: { To: { Address: string }[] }) => message.To.some((to) => to.Address === email))?.ID;
  }).toBeTruthy();
  const data = await (await request.get("http://127.0.0.1:58025/api/v1/messages")).json();
  const message = data.messages.find((message: { To: { Address: string }[] }) => message.To.some((to) => to.Address === email));
  const body = await (await request.get(`http://127.0.0.1:58025/api/v1/message/${message.ID}`)).json();
  const match = (body.HTML || body.Text).match(/https?:\/\/[^\s"<>]+\/auth\/v1\/verify\?[^\s"<>]+/);
  expect(match, "로컬 메일함의 실제 확인 링크").toBeTruthy();
  await page.goto(match![0].replaceAll("&amp;", "&"));
  await expect(page).toHaveURL(/\/dashboard$/);
  return email;
}

test("비로그인 사용자는 화면과 API에 접근할 수 없다", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /반가워요/, level: 1 })).toBeVisible();
  await page.screenshot({ path: "test-results/home.png", fullPage: true });
  for (const path of ["/dashboard", "/account"]) {
    await page.goto(path); await expect(page).toHaveURL(/\/login\?next=/);
    await expect(page.getByRole("heading", { name: "로그인", exact: true })).toBeVisible();
  }
  const response = await request.get("/api/private");
  expect(response.status()).toBe(401); expect(response.headers()["cache-control"]).toContain("no-store");
});

test("위조한 세션 쿠키는 인증으로 인정하지 않는다", async ({ page, context }) => {
  const forged = "base64-" + Buffer.from(JSON.stringify({ access_token: "forged.jwt.token", refresh_token: "forged", user: { id: "fake", email: "attacker@example.test" }, expires_at: 9999999999 })).toString("base64url");
  await context.addCookies([{ name: "sb-127-auth-token", value: forged, domain: "127.0.0.1", path: "/" }]);
  await page.goto("/account"); await expect(page).toHaveURL(/\/login/);
  expect((await context.request.get("/api/private")).status()).toBe(401);
});

test("가입·실제 확인 메일·로그인·계정·로그아웃이 동작한다", async ({ page, request, context }) => {
  const email = await register(page, request);
  await expect(page.getByText(email, { exact: true }).first()).toBeVisible();
  const authCookies = (await context.cookies()).filter((cookie) => cookie.name.includes("auth-token"));
  expect(authCookies.length).toBeGreaterThan(0);
  expect(authCookies.every((cookie) => cookie.httpOnly && cookie.sameSite === "Lax")).toBe(true);
  const api = await context.request.get("/api/private");
  expect(api.status()).toBe(200); expect((await api.json()).email).toBe(email);
  await page.goto("/account");
  await expect(page.getByRole("heading", { name: "기본 정보" })).toBeVisible();
  await page.getByRole("button", { name: "로그아웃" }).click(); await expect(page).toHaveURL(/\/login$/);
  expect((await context.request.get("/api/private")).status()).toBe(401);
  await page.goto("/account");
  await page.getByLabel("이메일", { exact: true }).fill(email);
  await page.getByLabel("비밀번호", { exact: true }).fill("wrong-password");
  await page.getByRole("button", { name: "로그인", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "로그인할 수 없습니다" })).toBeVisible();
  await expect(page.getByLabel("이메일", { exact: true })).toHaveValue(email);
  await page.getByLabel("비밀번호", { exact: true }).fill(password);
  await page.getByRole("button", { name: "로그인", exact: true }).click(); await expect(page).toHaveURL(/\/account$/);
  await page.reload(); await expect(page.getByRole("heading", { name: "계정", exact: true })).toBeVisible();
  const sessionCookie = (await context.cookies()).find((cookie) => cookie.name === "sb-127-auth-token");
  expect(sessionCookie, "저장된 세션 쿠키").toBeTruthy();
  const session = JSON.parse(Buffer.from(sessionCookie!.value.slice("base64-".length), "base64url").toString());
  session.expires_at = Math.floor(Date.now() / 1000) - 60;
  await context.addCookies([{ ...sessionCookie!, value: "base64-" + Buffer.from(JSON.stringify(session)).toString("base64url") }]);
  const refreshed = await context.request.get("/api/private");
  expect(refreshed.status()).toBe(200); expect((await refreshed.json()).email).toBe(email);
  const renewed = (await context.cookies()).find((cookie) => cookie.name === "sb-127-auth-token");
  const renewedSession = JSON.parse(Buffer.from(renewed!.value.slice("base64-".length), "base64url").toString());
  expect(renewedSession.expires_at).toBeGreaterThan(Math.floor(Date.now() / 1000));
});

test("외부 목적지와 잘못된 확인 링크를 안전하게 처리한다", async ({ page }) => {
  await page.goto("/login?next=https://evil.test");
  expect(await page.locator('input[name="next"]').inputValue()).toBe("/dashboard");
  await page.goto("/auth/callback?next=//evil.test");
  await expect(page).toHaveURL(/\/login\?error=confirmation$/);
  await expect(page.getByRole("alert").filter({ hasText: "확인 링크" })).toBeVisible();
  await page.goto("/auth/confirm?type=recovery&token_hash=bad&next=https://evil.test");
  await expect(page).toHaveURL(/\/login\?error=confirmation$/);
});

test("모바일에서도 로그인 양식을 사용할 수 있다", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await expect(page.getByLabel("이메일", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/login-mobile.png", fullPage: true });
});
