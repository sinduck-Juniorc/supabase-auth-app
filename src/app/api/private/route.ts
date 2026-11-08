import { NextResponse } from "next/server";
import { authenticatedUser } from "@/lib/auth";

export const dynamic = "force-dynamic";
export async function GET() {
  const user = await authenticatedUser();
  const headers = { "Cache-Control": "private, no-store, max-age=0" };
  if (!user) return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401, headers });
  return NextResponse.json({ message: "로그인한 사용자에게만 제공하는 응답입니다.", userId: user.id, email: user.email }, { headers });
}
