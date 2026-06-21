# Final pilot: expert adjudication and evaluation

This documents the expert-adjudication final-target layer and the one-time final
evaluation. All work uses only sanitized, non-synthetic fields. Worker labels
are never modified.

## Expert adjudication layer

`ExpertAdjudication` is an additive final-target table (Postgres + SQLite
migrations under `prisma/`). It never overwrites a worker `MessageLabel`. One row
per message stores the adjudicator id (`claude-code-expert`), the candidate
reason, the final risk level / scam type / red flags / recommended action /
plain-English warning, a rationale, and a compact PII-free snapshot of the
worker-label evidence considered.

The expert judgments live in `scripts/expert_adjudications.json` (no raw message
bodies — final-target fields, rationale, and provenance only).
`scripts/adjudicate_messages.py` is idempotent: it finds the current candidate
messages (reviewable and either single-label, no-label, low-agreement, or
otherwise ambiguous), validates each judgment against the app vocabularies in
`lib/constants.ts`, upserts on the unique `messageId`, and prints counts only.

Two reviewable-but-unusable candidates are intentionally excluded (recorded in
`_excluded`): one keyboard-mash gibberish body and one incomplete one-line
conversational fragment with no link, request, or context.

## Final target precedence

`scripts/build_wave2_dataset.py` freezes a versioned snapshot. For each real
message the final target is, in order:

1. the expert adjudication, when one exists;
2. otherwise worker consensus, when it clears the quality gate (≥2 independent
   labels and ≥50% agreement on both risk level and scam type);
3. otherwise the message is excluded.

Every exported row and the manifest record provenance (`expert_adjudication` or
`worker_consensus`). The split is a deterministic, message-level 70/15/15
train/validation/test split. The test split is reserved untouched and used once.

## Live vs. frozen

Collection and labeling are live, so operational counts (real messages, saved
labels, expert adjudications, labels-per-message) drift continuously. The frozen
snapshot is immutable once built. The deck and `trustfall-metrics.json` report
the two separately, plus consensus-vs-expert example counts and the small-data
limitation.

## Small-data limitation

The frozen test split is tiny. Reported test metrics are a directional pilot
signal, not a statistically robust benchmark; do not read accuracy deltas on a
single-digit test set as production evidence.
