import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { safeNext } from "@/lib/auth-paths";
import { getConfig } from "@/lib/config";

export async function GET(request: NextRequest) {
  const hash = request.nextUrl.searchParams.get("token_hash");
  const type = request.nextUrl.searchParams.get("type");
  const { appUrl } = getConfig();
  const next = safeNext(request.nextUrl.searchParams.get("next"));
  if (hash && hash.length <= 512 && (type === "email" || type === "signup")) {
    const supabase = await createClient();
    const { error } = await supabase.auth.verifyOtp({ token_hash: hash, type });
    if (!error) return NextResponse.redirect(new URL(next, appUrl), { status: 303, headers: { "Cache-Control": "no-store" } });
  }
  return NextResponse.redirect(new URL("/login?error=confirmation", appUrl), { status: 303, headers: { "Cache-Control": "no-store" } });
}
