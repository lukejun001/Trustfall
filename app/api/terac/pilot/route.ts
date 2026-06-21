import { NextResponse } from "next/server";
import { z } from "zod";
import { teracPilot } from "@/lib/terac-api";
export const dynamic = "force-dynamic";
export async function GET() { try { return NextResponse.json({ ok: true, data: await teracPilot("list_projects", {}) }); } catch (error) { return NextResponse.json({ ok: false, error: error instanceof Error ? error.message : "Terac request failed" }, { status: 502 }); } }
const body = z.object({ action: z.enum(["create_project", "create_wave1_draft", "launch_wave1"]), projectId: z.string().optional(), opportunityId: z.string().optional(), participants: z.number().int().optional(), taskUrl: z.string().url().optional() });
export async function POST(request: Request) { try { const input = body.parse(await request.json()); return NextResponse.json({ ok: true, data: await teracPilot(input.action, input) }); } catch (error) { return NextResponse.json({ ok: false, error: error instanceof Error ? error.message : "Invalid pilot request" }, { status: error instanceof z.ZodError ? 400 : 502 }); } }
