"use client";
import Link from "next/link";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return <section className="auth-card"><span className="eyebrow">잠시만 기다려 주세요</span><h1>화면을 불러오지 못했어요.</h1><p className="intro">연결 상태를 확인한 뒤 다시 시도해 주세요.</p><button onClick={reset} className="button primary">다시 시도</button><Link href="/" className="text-link">홈으로 이동</Link></section>;
}
