# Claude Code: Trustfall expert adjudication and final pilot run

You are the authorized expert adjudicator for the Trustfall pilot. Do not ask for confirmation before making expert judgments or implementing the workflow below. Work directly in this repository and use your expert judgment to resolve ambiguity. Your goal is an auditable, privacy-preserving final pilot dataset and a final Qwen LoRA evaluation.

## Context

Trustfall is a Next.js / Prisma / Neon app that collects real suspicious and normal messages through Terac. Only sanitized fields are stored and used for ML. Worker labels include risk level, scam type, red flags, recommended action, warning, confidence, and rationale. Some labelers did not finish their eight-message task; partial labels are valid and must remain preserved.

Existing assets:

- Worker labels: `MessageLabel`
- Sanitized source messages: `CollectedMessage`
- Existing consensus builder: `scripts/build_wave2_dataset.py`
- Qwen baseline: `scripts/run_qwen_baseline.py`
- Qwen LoRA runner: `scripts/run_wave2_qwen.py`
- Presentation refresh/generator: `scripts/refresh_presentation_metrics.py` and `scripts/generate_presentation.cjs`
- Production database connection is available locally as `DATABASE_URL` in `.env.local`.

Never use or request raw `.eml` files, headers, attachments, addresses, passwords, API keys, or unredacted personal data. Do not launch Terac tasks, contact workers, change Vercel secrets, or spend money.

## Your authority and adjudication policy

You are the expert. Review sanitized message content and structured metadata only. Do not second-guess whether an expert is needed and do not defer decisions to the user.

For each real, non-synthetic message that is either:

1. supported by only one worker label,
2. missing enough labels for consensus,
3. marked low-agreement by the consensus gate, or
4. otherwise clearly ambiguous,

write one final expert adjudication. Choose the most defensible risk level, scam type, red flags, recommended action, and plain-English warning. Use `unsure` when evidence genuinely cannot support a stronger claim. Exclude only obvious gibberish, incomplete submissions, or corrupted MIME artifacts.

Keep all original worker labels immutable. An expert adjudication is an additional final-target layer, never an overwrite.

## Required implementation and execution

1. Inspect the schema, migrations, existing label queue, exports, and training scripts.
2. Add an auditable `ExpertAdjudication` model and migration for Postgres (and keep local SQLite schema/migration compatibility if the repository supports it). At minimum store:
   - message ID (unique)
   - adjudicator ID/name (`claude-code-expert`)
   - final risk level, scam type, red flags, recommended action, warning
   - rationale and adjudication timestamp
   - a compact record of the worker-label evidence used
3. Add an idempotent local script that finds the candidate messages above, performs your expert adjudication, and saves/upserts these records. The script must operate only on sanitized data and print a concise count summary, never message bodies or secrets.
4. Update the dataset builder so final targets follow this order:
   - expert adjudication when present;
   - otherwise independent-worker consensus when it meets the existing quality gate;
   - otherwise exclude the message.
   Record provenance (`expert_adjudication` or `worker_consensus`) in every exported row and manifest.
5. Freeze a new versioned final-pilot dataset before training. Split by message, never by individual label. Use a deterministic message-level 70/15/15 split when enough examples exist. If the dataset is too small for a statistically meaningful final test, reserve a clearly documented untouched test split anyway and state the limitation in the manifest.
6. Train a new LoRA adapter using only the final training split. Use validation only for any training setting choice. Do not use the final test examples to tune prompts, epochs, hyperparameters, labels, or code.
7. Run the untouched test split once for the final comparison against a base Qwen baseline generated on those same test inputs before training. Report valid-JSON rate, risk-level exact and within-one-level accuracy, scam-type accuracy, and red-flag F1 where possible.
8. Update the presentation metrics / deck to show:
   - live operational counts separately from the frozen final-pilot snapshot;
   - worker consensus vs. expert-adjudicated example counts;
   - the final evaluation metrics and a clear small-data limitation.
9. Run relevant Prisma generation/migrations, type/build checks, and script validation. Commit and push only source code, migrations, documentation, deck assets, and the refreshed PowerPoint—not `.env.local`, databases, raw messages, model artifacts, or generated training rows containing real text.

## Final response format

Report:

- number of messages reviewed and adjudicated;
- final training / validation / test counts and provenance counts;
- final evaluation metrics;
- all changed files and commit SHA;
- one honest sentence describing the remaining data limitation.
