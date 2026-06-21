import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { isReviewableForLabeling } from "@/lib/review";

export const dynamic = "force-dynamic";

export async function GET() {
  const required = Number(process.env.LABELS_PER_PARTICIPANT ?? 8) || 8;
  const messages = await prisma.collectedMessage.findMany({
    where: { isSyntheticTestFixture: false },
    select: { sanitizedText: true },
  });
  const eligibleMessages = messages.filter((message) =>
    isReviewableForLabeling(message.sanitizedText),
  ).length;

  return NextResponse.json({
    ready: eligibleMessages >= required,
    realMessages: eligibleMessages,
    labelsPerParticipant: required,
    remainingMessages: Math.max(0, required - eligibleMessages),
  });
}
