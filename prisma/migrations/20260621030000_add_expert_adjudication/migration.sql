-- CreateTable
CREATE TABLE "ExpertAdjudication" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "messageId" TEXT NOT NULL,
    "adjudicatorId" TEXT NOT NULL DEFAULT 'claude-code-expert',
    "candidateReason" TEXT NOT NULL,
    "riskLevel" TEXT NOT NULL,
    "scamType" TEXT NOT NULL,
    "redFlags" TEXT NOT NULL,
    "recommendedAction" TEXT NOT NULL,
    "plainEnglishWarning" TEXT NOT NULL,
    "rationale" TEXT NOT NULL,
    "evidence" TEXT NOT NULL,
    "adjudicatedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ExpertAdjudication_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "CollectedMessage" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "ExpertAdjudication_messageId_key" ON "ExpertAdjudication"("messageId");
