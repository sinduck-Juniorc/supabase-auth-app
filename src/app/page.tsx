import Link from "next/link";

export default function Home() {
  return <div className="home"><section className="hero">
    <span className="eyebrow">나만을 위한 시작</span>
    <h1>반가워요.<br /><span>나만의 공간</span>에<br />들어오세요.</h1>
    <p>계정을 만들고, 로그인하고, 내 정보를 한곳에서 확인하세요.</p>
    <div className="actions"><Link className="button primary" href="/signup">계정 만들기 <span aria-hidden>↗</span></Link><Link className="button secondary" href="/login">로그인</Link></div>
  </section><section className="preview-card" aria-label="서비스 소개">
    <div className="card-top"><span className="status-dot" /> 나의 공간</div>
    <div className="avatar">나</div><h2>다시 만나서 반가워요</h2><p>로그인하면 나만의 계정 공간이 열립니다.</p>
    <div className="feature-row"><span className="feature-icon">01</span><div><strong>간편한 시작</strong><small>이메일로 계정을 만들어요</small></div><span aria-hidden>✓</span></div>
    <div className="feature-row"><span className="feature-icon">02</span><div><strong>나만의 계정</strong><small>로그인 후 정보를 확인해요</small></div><span aria-hidden>✓</span></div>
    <Link href="/dashboard" prefetch={false} className="text-link">내 공간 둘러보기 →</Link>
  </section></div>;
}
