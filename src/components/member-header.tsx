import { signout } from "@/app/auth/actions";

export function MemberHeader({ email }: { email?: string }) {
  return <div className="member-header"><span className="badge"><span className="status-dot" /> 로그인됨</span><span className="member-email">{email}</span><form action={signout}><button className="button small secondary" type="submit">로그아웃</button></form></div>;
}
