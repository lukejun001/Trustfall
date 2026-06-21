-- CreateTable
CREATE TABLE "ExpertAdjudication" (
    "id" TEXT NOT NULL,
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
    "adjudicatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ExpertAdjudication_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ExpertAdjudication_messageId_key" ON "ExpertAdjudication"("messageId");

-- AddForeignKey
ALTER TABLE "ExpertAdjudication" ADD CONSTRAINT "ExpertAdjudication_messageId_fkey" FOREIGN KEY ("messageId") REFERENCES "CollectedMessage"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
