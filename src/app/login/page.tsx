import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { authenticatedUser } from "@/lib/auth";
import { safeNext } from "@/lib/auth-paths";

export const dynamic = "force-dynamic";
export default async function Login({ searchParams }: { searchParams: Promise<{ next?: string; error?: string }> }) {
  const params = await searchParams;
  const next = safeNext(params.next);
  if (await authenticatedUser()) redirect(next);
  return <section className="auth-card"><span className="eyebrow">다시 오신 것을 환영해요</span><h1>로그인</h1><p className="intro">나만의 공간으로 이어집니다.</p><AuthForm mode="login" next={next} confirmationError={params.error === "confirmation"} /></section>;
}
