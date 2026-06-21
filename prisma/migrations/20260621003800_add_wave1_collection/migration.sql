-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_TeracParticipant" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "teracSubmissionId" TEXT,
    "startedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completedAt" DATETIME,
    "collectionCompletedAt" DATETIME,
    "wave" TEXT NOT NULL DEFAULT 'collect',
    "status" TEXT NOT NULL DEFAULT 'started'
);
INSERT INTO "new_TeracParticipant" ("completedAt", "id", "startedAt", "status", "teracSubmissionId") SELECT "completedAt", "id", "startedAt", "status", "teracSubmissionId" FROM "TeracParticipant";
DROP TABLE "TeracParticipant";
ALTER TABLE "new_TeracParticipant" RENAME TO "TeracParticipant";
CREATE UNIQUE INDEX "TeracParticipant_teracSubmissionId_key" ON "TeracParticipant"("teracSubmissionId");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
