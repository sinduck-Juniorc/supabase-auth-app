import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { MemberHeader } from "@/components/member-header";

export const dynamic = "force-dynamic";
export default async function Account({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const user = await requireUser("/account");
  const params = await searchParams;
  return <section className="workspace"><MemberHeader email={user.email} /><span className="eyebrow">나의 정보</span><h1>계정</h1><p className="intro">내 계정의 기본 정보를 확인하세요.</p>
    {params.error === "logout" && <p className="notice error" role="alert">로그아웃하지 못했습니다. 잠시 후 다시 시도해 주세요.</p>}
    <div className="panel account-panel"><div className="avatar">나</div><h2>기본 정보</h2><dl><div><dt>이메일</dt><dd>{user.email}</dd></div><div><dt>계정 식별자</dt><dd>{user.id}</dd></div><div><dt>이메일 상태</dt><dd>{user.email_confirmed_at ? "확인됨" : "확인 필요"}</dd></div></dl><Link href="/dashboard" className="text-link">← 내 공간으로</Link></div>
  </section>;
}
