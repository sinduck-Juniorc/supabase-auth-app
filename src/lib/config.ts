import "server-only";

export function getConfig() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  const app = process.env.APP_URL;
  if (!url || !key || !app) throw new Error(".env.local의 Supabase와 APP_URL 설정이 필요합니다.");
  const origin = new URL(app);
  if (!["http:", "https:"].includes(origin.protocol) || origin.username || origin.password ||
      origin.pathname !== "/" || origin.search || origin.hash) throw new Error("APP_URL은 앱의 기본 주소여야 합니다.");
  if (origin.protocol === "http:" && !["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname)) {
    throw new Error("배포 주소에는 HTTPS가 필요합니다.");
  }
  return { url, key, appUrl: origin.origin, secure: origin.protocol === "https:" };
}
