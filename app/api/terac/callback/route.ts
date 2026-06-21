import { NextResponse } from "next/server";
import { teracCallbackUrl } from "@/lib/terac";
export async function GET(request: Request) { const id = new URL(request.url).searchParams.get("teracSubmissionId"); if (!id) return NextResponse.json({ error: "Missing teracSubmissionId" }, { status: 400 }); return NextResponse.redirect(new URL(teracCallbackUrl(id), request.url)); }
