import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { getConfig } from "@/lib/config";
import { isProtectedPath, loginPath } from "@/lib/auth-paths";

export async function proxy(request: NextRequest) {
  const config = getConfig();
  let response = NextResponse.next({ request });
  const supabase = createServerClient(config.url, config.key, {
    cookieOptions: { httpOnly: true, sameSite: "lax", secure: config.secure, path: "/" },
    global: { fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }) },
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(values, headers) {
        values.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        values.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
        Object.entries(headers).forEach(([key, value]) => response.headers.set(key, value));
      },
    },
  });
  const { data, error } = await supabase.auth.getUser();
  const valid = !error && data.user && !data.user.is_anonymous;
  if (isProtectedPath(request.nextUrl.pathname) && !valid) {
    const denied = request.nextUrl.pathname.startsWith("/api/")
      ? NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 })
      : NextResponse.redirect(new URL(loginPath(request.nextUrl.pathname), config.appUrl));
    response.cookies.getAll().forEach((cookie) => denied.cookies.set(cookie));
    denied.headers.set("Cache-Control", "private, no-store, max-age=0");
    return denied;
  }
  response.headers.set("Cache-Control", "private, no-store, max-age=0");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
