"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { getConfig } from "@/lib/config";
import { readCredentials, safeNext } from "@/lib/auth-paths";

export type AuthState = { error?: string; notice?: string };

export async function login(_state: AuthState, form: FormData): Promise<AuthState> {
  const credentials = readCredentials(form);
  if (!credentials) return { error: "이메일과 비밀번호를 확인해 주세요." };
  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword(credentials);
  if (error) return { error: "로그인할 수 없습니다. 입력 내용과 이메일 인증 여부를 확인해 주세요." };
  revalidatePath("/", "layout");
  redirect(safeNext(form.get("next")));
}

export async function signup(_state: AuthState, form: FormData): Promise<AuthState> {
  const credentials = readCredentials(form, true);
  if (!credentials) return { error: "이메일과 12~128자의 비밀번호, 비밀번호 확인을 다시 확인해 주세요." };
  const supabase = await createClient();
  const { appUrl } = getConfig();
  const next = safeNext(form.get("next"));
  const { data, error } = await supabase.auth.signUp({ ...credentials,
    options: { emailRedirectTo: `${appUrl}/auth/callback?${new URLSearchParams({ next })}` },
  });
  if (error) return { error: "가입 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요." };
  if (data.session) {
    revalidatePath("/", "layout");
    redirect(next);
  }
  return { notice: "가입 요청을 받았습니다. 이메일의 확인 링크를 눌러 가입을 마쳐 주세요." };
}

export async function signout() {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut({ scope: "local" });
  if (error) redirect("/account?error=logout");
  revalidatePath("/", "layout");
  redirect("/login");
}
