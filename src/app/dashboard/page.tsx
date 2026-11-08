import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { MemberHeader } from "@/components/member-header";

export const dynamic = "force-dynamic";
export default async function Dashboard() {
  const user = await requireUser("/dashboard");
  return <section className="workspace"><MemberHeader email={user.email} /><span className="eyebrow">나의 공간</span><h1>다시 만나서 반가워요.</h1><p className="intro">계정에 연결된 나만의 공간입니다.</p><div className="dashboard-grid">
    <article className="panel"><span className="large-icon">◈</span><h2>시작할 준비가 됐어요</h2><p>로그인을 마쳤습니다. 계정 정보를 확인하고 나만의 활동을 시작하세요.</p><Link href="/account" className="button primary">계정 정보 확인 →</Link></article>
    <article className="panel tinted"><span className="eyebrow">내 계정</span><h2>{user.email}</h2><p>가입 이메일로 내 계정을 확인할 수 있어요.</p><div className="detail-line"><span>이메일 확인</span><strong>{user.email_confirmed_at ? "확인됨" : "확인 필요"}</strong></div></article>
  </div></section>;
}
