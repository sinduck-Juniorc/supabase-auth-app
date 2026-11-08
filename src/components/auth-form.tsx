"use client";

import { useActionState, useState } from "react";
import Link from "next/link";
import { login, signup, type AuthState } from "@/app/auth/actions";

export function AuthForm({ mode, next, confirmationError = false }: { mode: "login" | "signup"; next: string; confirmationError?: boolean }) {
  const registering = mode === "signup";
  const [email, setEmail] = useState("");
  const [state, action, pending] = useActionState<AuthState, FormData>(registering ? signup : login, {});
  return <>
    {confirmationError && <p className="notice error" role="alert">확인 링크가 유효하지 않거나 만료됐습니다. 가입한 계정으로 로그인하거나 새 확인 링크를 요청해 주세요.</p>}
    <form action={action} className="auth-form" aria-busy={pending}>
      <input type="hidden" name="next" value={next} />
      <label htmlFor="email">이메일</label><input id="email" name="email" type="email" autoComplete="email" required maxLength={254} placeholder="name@example.com" value={email} onChange={(event) => setEmail(event.target.value)} />
      <label htmlFor="password">비밀번호</label><input id="password" name="password" type="password" autoComplete={registering ? "new-password" : "current-password"} required minLength={registering ? 12 : 1} maxLength={128} aria-describedby={registering ? "password-help" : undefined} />
      {registering && <><small id="password-help">12자 이상, 128자 이하로 입력해 주세요.</small><label htmlFor="confirmPassword">비밀번호 확인</label><input id="confirmPassword" name="confirmPassword" type="password" autoComplete="new-password" required minLength={12} maxLength={128} /></>}
      {state.error && <p className="notice error" role="alert">{state.error}</p>}
      {state.notice && <p className="notice success" role="status">{state.notice}</p>}
      <button className="button primary" type="submit" disabled={pending}>{pending ? "처리 중…" : registering ? "계정 만들기" : "로그인"}<span aria-hidden>→</span></button>
    </form>
    <p className="form-switch">{registering ? "이미 계정이 있으신가요?" : "처음 방문하셨나요?"} <Link href={`${registering ? "/login" : "/signup"}?${new URLSearchParams({ next })}`}>{registering ? "로그인" : "계정 만들기"}</Link></p>
  </>;
}
