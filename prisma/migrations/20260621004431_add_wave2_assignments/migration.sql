-- AlterTable
ALTER TABLE "TeracParticipant" ADD COLUMN "labelCompletedAt" DATETIME;

-- CreateTable
CREATE TABLE "LabelAssignment" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "participantId" TEXT NOT NULL,
    "messageId" TEXT NOT NULL,
    "position" INTEGER NOT NULL,
    "assignedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" DATETIME,
    CONSTRAINT "LabelAssignment_participantId_fkey" FOREIGN KEY ("participantId") REFERENCES "TeracParticipant" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "LabelAssignment_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "CollectedMessage" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "LabelAssignment_participantId_messageId_key" ON "LabelAssignment"("participantId", "messageId");

-- CreateIndex
CREATE UNIQUE INDEX "LabelAssignment_participantId_position_key" ON "LabelAssignment"("participantId", "position");
