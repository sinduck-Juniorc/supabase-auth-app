import "server-only";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { getConfig } from "@/lib/config";

export async function createClient() {
  const config = getConfig();
  const store = await cookies();
  return createServerClient(config.url, config.key, {
    cookieOptions: { httpOnly: true, sameSite: "lax", secure: config.secure, path: "/" },
    global: { fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }) },
    cookies: {
      getAll: () => store.getAll(),
      setAll(values) {
        try {
          values.forEach(({ name, value, options }) => store.set(name, value, options));
        } catch {
          // Server Component는 쓰기 불가. 요청 앞단의 proxy가 갱신 쿠키를 전달한다.
        }
      },
    },
  });
}
