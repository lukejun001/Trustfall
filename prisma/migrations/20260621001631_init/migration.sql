-- CreateTable
CREATE TABLE "TeracParticipant" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "teracSubmissionId" TEXT,
    "startedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" DATETIME,
    "status" TEXT NOT NULL DEFAULT 'started'
);

-- CreateTable
CREATE TABLE "CollectedMessage" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "submittedByParticipantId" TEXT NOT NULL,
    "sanitizedText" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "initialUserBelief" TEXT NOT NULL,
    "shortContext" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "CollectedMessage_submittedByParticipantId_fkey" FOREIGN KEY ("submittedByParticipantId") REFERENCES "TeracParticipant" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "MessageLabel" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "messageId" TEXT NOT NULL,
    "labeledByParticipantId" TEXT NOT NULL,
    "riskLevel" TEXT NOT NULL,
    "scamType" TEXT NOT NULL,
    "redFlags" TEXT NOT NULL,
    "recommendedAction" TEXT NOT NULL,
    "plainEnglishWarning" TEXT NOT NULL,
    "confidence" INTEGER NOT NULL,
    "rationale" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "MessageLabel_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "CollectedMessage" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "MessageLabel_labeledByParticipantId_fkey" FOREIGN KEY ("labeledByParticipantId") REFERENCES "TeracParticipant" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "QualityFlag" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "targetType" TEXT NOT NULL,
    "targetId" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateIndex
CREATE UNIQUE INDEX "TeracParticipant_teracSubmissionId_key" ON "TeracParticipant"("teracSubmissionId");

-- CreateIndex
CREATE UNIQUE INDEX "MessageLabel_messageId_labeledByParticipantId_key" ON "MessageLabel"("messageId", "labeledByParticipantId");
