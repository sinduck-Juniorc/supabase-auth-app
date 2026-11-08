import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = { title: "안심 앱", description: "나만의 공간으로 이어지는 간편한 로그인" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko"><body>
    <header className="header"><Link href="/" className="brand"><span className="brand-icon">◈</span> 안심 앱</Link>
      <nav aria-label="주 메뉴"><Link href="/">홈</Link><Link href="/dashboard" prefetch={false}>내 공간</Link><Link href="/account" prefetch={false}>계정</Link></nav>
    </header>
    <main>{children}</main>
    <footer>안심 앱 · 계정 서비스</footer>
  </body></html>;
}
