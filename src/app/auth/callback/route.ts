import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { safeNext } from "@/lib/auth-paths";
import { getConfig } from "@/lib/config";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const { appUrl } = getConfig();
  const next = safeNext(request.nextUrl.searchParams.get("next"));
  if (code && code.length <= 8192) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) return NextResponse.redirect(new URL(next, appUrl), { status: 303, headers: { "Cache-Control": "no-store" } });
  }
  return NextResponse.redirect(new URL("/login?error=confirmation", appUrl), { status: 303, headers: { "Cache-Control": "no-store" } });
}
