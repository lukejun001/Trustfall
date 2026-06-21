import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
const labelsPerParticipant = () => { const n = Number(process.env.LABELS_PER_PARTICIPANT ?? 8); return Number.isInteger(n) && n > 0 ? n : 8; };
export async function GET(request: Request) {
  const id = new URL(request.url).searchParams.get("teracSubmissionId"); if (!id) return NextResponse.json({ error: "Missing participant ID" }, { status: 400 });
  const required = labelsPerParticipant();
  const participant = await prisma.teracParticipant.upsert({ where: { teracSubmissionId: id }, update: { wave: "label" }, create: { teracSubmissionId: id, wave: "label", status: "label_started" } });
  let assignments = await prisma.labelAssignment.findMany({ where: { participantId: participant.id }, include: { message: { select: { id: true, sanitizedText: true, source: true, shortContext: true } } }, orderBy: { position: "asc" } });
  if (!assignments.length) {
    const candidates = await prisma.collectedMessage.findMany({ where: { isSyntheticTestFixture: false, submittedByParticipantId: { not: participant.id }, labels: { none: { labeledByParticipantId: participant.id } }, assignments: { none: { participantId: participant.id } } }, include: { _count: { select: { labels: true } } } });
    if (candidates.length < required) return NextResponse.json({ ready: false, required, available: candidates.length, messages: [] });
    const shuffled = candidates.sort((a, b) => a._count.labels - b._count.labels || Math.random() - 0.5).slice(0, required);
    await prisma.$transaction(shuffled.map((message, position) => prisma.labelAssignment.create({ data: { participantId: participant.id, messageId: message.id, position } })));
    assignments = await prisma.labelAssignment.findMany({ where: { participantId: participant.id }, include: { message: { select: { id: true, sanitizedText: true, source: true, shortContext: true } } }, orderBy: { position: "asc" } });
  }
  const completed = assignments.filter(assignment => assignment.completedAt).length;
  return NextResponse.json({ ready: true, required, completed, messages: assignments.map(assignment => ({ ...assignment.message, assignmentId: assignment.id, completed: Boolean(assignment.completedAt) })) });
}
