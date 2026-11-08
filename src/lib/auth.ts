import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { loginPath } from "@/lib/auth-paths";

export const authenticatedUser = cache(async () => {
  const supabase = await createClient();
  // 쿠키의 user 객체를 신뢰하지 않고 Auth 서버에 검증을 요청한다.
  const { data, error } = await supabase.auth.getUser();
  return !error && data.user && !data.user.is_anonymous ? data.user : null;
});

export async function requireUser(next: string) {
  const user = await authenticatedUser();
  if (!user) redirect(loginPath(next));
  return user;
}
