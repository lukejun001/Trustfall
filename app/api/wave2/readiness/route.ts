import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
export const dynamic = "force-dynamic";
export async function GET() { const required = Number(process.env.LABELS_PER_PARTICIPANT ?? 8) || 8; const messages = await prisma.collectedMessage.count({ where: { isSyntheticTestFixture: false } }); return NextResponse.json({ ready: messages >= required, realMessages: messages, labelsPerParticipant: required, remainingMessages: Math.max(0, required - messages) }); }
