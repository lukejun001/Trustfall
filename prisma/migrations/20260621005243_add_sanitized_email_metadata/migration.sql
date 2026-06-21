-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_CollectedMessage" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "submittedByParticipantId" TEXT NOT NULL,
    "sanitizedText" TEXT NOT NULL,
    "inputMethod" TEXT NOT NULL DEFAULT 'text_paste',
    "sanitizedSubject" TEXT,
    "sanitizedBody" TEXT,
    "source" TEXT NOT NULL,
    "initialUserBelief" TEXT NOT NULL,
    "shortContext" TEXT,
    "fromDomain" TEXT,
    "replyToDomain" TEXT,
    "returnPathDomain" TEXT,
    "fromReplyToMismatch" BOOLEAN,
    "linkFeatures" TEXT,
    "authSummary" TEXT,
    "hasAttachments" BOOLEAN NOT NULL DEFAULT false,
    "attachmentExtensions" TEXT,
    "attachmentsStripped" BOOLEAN NOT NULL DEFAULT true,
    "emlParsedClientSide" BOOLEAN,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "CollectedMessage_submittedByParticipantId_fkey" FOREIGN KEY ("submittedByParticipantId") REFERENCES "TeracParticipant" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_CollectedMessage" ("createdAt", "id", "initialUserBelief", "sanitizedText", "shortContext", "source", "submittedByParticipantId") SELECT "createdAt", "id", "initialUserBelief", "sanitizedText", "shortContext", "source", "submittedByParticipantId" FROM "CollectedMessage";
DROP TABLE "CollectedMessage";
ALTER TABLE "new_CollectedMessage" RENAME TO "CollectedMessage";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
