import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { authenticatedUser } from "@/lib/auth";
import { safeNext } from "@/lib/auth-paths";

export const dynamic = "force-dynamic";
export default async function Signup({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const params = await searchParams;
  const next = safeNext(params.next);
  if (await authenticatedUser()) redirect(next);
  return <section className="auth-card"><span className="eyebrow">함께 시작해요</span><h1>계정 만들기</h1><p className="intro">이메일을 확인하면 가입이 마무리됩니다.</p><AuthForm mode="signup" next={next} /></section>;
}
