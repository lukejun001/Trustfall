# Trustfall: a question tree from zero knowledge to full understanding

Read this in order. Every answer points to the most useful next question; indented questions are optional deep dives. If you can answer every bold question in your own words, you understand the project end to end.

---

## 0. Start with no context

### Q0.1 — What is Trustfall?

Trustfall is a privacy-first workflow for improving scam-safety AI. It collects examples of real suspicious and normal messages, sanitizes them, asks independent humans to label them, then uses the resulting dataset to adapt and evaluate a small language model.

**Next:** Q0.2

### Q0.2 — What problem is it trying to solve?

Scam messages are contextual: sender mismatches, urgency, links, requests for codes, and social pressure all matter together. Generic datasets can miss the messy details people actually see. Trustfall tries to learn from real-world signals without treating private inboxes as raw training material.

**Next:** Q0.3

### Q0.3 — Is Trustfall itself a finished consumer scam detector?

No. It is a working pilot and data-to-model workflow. The current product demonstrates that it can collect privacy-protected examples, obtain human judgments, create an auditable training snapshot, and compare a baseline Qwen model with a LoRA-adapted version.

**Next:** Q0.4

### Q0.4 — What is the one-sentence project story?

“Trustfall turns sanitized real-world message signals into human consensus and measured scam-safety model improvement.”

**Next:** Q1.1

---

## 1. The outside services

### Q1.1 — What is Terac?

Terac is the participant-work platform used for this pilot. It recruits participants and sends them to Trustfall task URLs. Trustfall uses it for two separate jobs: collecting examples in Wave 1 and labeling other people’s redacted examples in Wave 2.

**Next:** Q1.2

### Q1.2 — Why not collect data directly from random website visitors?

Terac gives the pilot a structured participant workflow, task tracking, and controlled recruitment. It makes it possible to compensate people for collection and labeling work rather than hoping anonymous visitors provide usable data.

**Next:** Q1.3

### Q1.3 — What does Terac not do?

Terac is not the database, the redaction system, the labeling logic, or the model-training system. It routes participants to Trustfall. The Trustfall app controls what is stored and how labels become training targets.

**Next:** Q1.4

### Q1.4 — What is Vercel doing?

Vercel hosts the public Next.js application at `trustfall-8eks.vercel.app`. It serves the collection, labeling, demo, API, and export routes.

**Next:** Q1.5

### Q1.5 — What is Neon doing?

Neon hosts the production Postgres database. It stores sanitized message records, participant records, label assignments, worker labels, quality flags, and expert adjudications. It does not need to store raw email files.

**Next:** Q1.6

### Q1.6 — What is GitHub doing?

GitHub is the source-of-truth code repository. It contains application code, Prisma migrations, training scripts, documentation, presentation assets, and the PowerPoint deck. It intentionally excludes credentials, raw messages, model artifacts, and generated real-text datasets.

**Next:** Q2.1

---

## 2. The two-wave participant journey

### Q2.1 — What is Wave 1?

Wave 1 is message collection. A participant submits one suspicious and one normal message using the Trustfall collection interface. The app accepts pasted content or a local `.eml` upload, but raw `.eml` files are parsed in the browser and are not sent to the server.

**Next:** Q2.2

### Q2.2 — Why collect both suspicious and normal messages?

A detector needs contrast. If it only sees scams, it may learn that ordinary language is suspicious. Normal examples help the model distinguish legitimate notices from messages that merely sound urgent or transactional.

**Next:** Q2.3

### Q2.3 — What is Wave 2?

Wave 2 is independent human labeling. A participant sees redacted messages submitted by other people and labels risk level, scam type, red flags, recommended action, warning, confidence, and rationale.

**Next:** Q2.4

### Q2.4 — Why must Wave 2 participants label other people’s messages?

It reduces self-justification bias. Someone who submitted a message may be attached to their initial judgment. Independent reviewers provide a more useful signal for a consensus target.

**Next:** Q2.5

### Q2.5 — How many messages does a Wave 2 worker see?

The pilot task is designed for eight messages per labeler. The queue preferentially assigns messages with fewer labels so coverage becomes more balanced over time.

**Next:** Q2.6

### Q2.6 — What happens if a worker stops halfway through?

Each individual label saves immediately. A partial worker is not wasted: saved labels remain in the database. Only the unfinished assignments remain incomplete.

**Next:** Q2.7

### Q2.7 — Does “15 labelers recruited” always mean 30 consensus-labeled messages?

No. Fifteen eight-message tasks create 120 possible labels, but people can abandon tasks, labels can concentrate unevenly, and messages may be excluded for unreadability or disagreement. The database’s saved-label count—not recruitment count—is the real evidence.

**Next:** Q3.1

---

## 3. Privacy and redaction

### Q3.1 — What is Trustfall’s central privacy promise?

The system tries to preserve scam-relevant evidence while removing unnecessary personal identity. The model pipeline uses sanitized text and structured security features, not raw inbox material.

**Next:** Q3.2

### Q3.2 — What happens to an uploaded `.eml` file?

The browser parses it locally. Trustfall extracts relevant content and metadata, sanitizes those fields, and sends only the resulting sanitized record. The raw file, full header history, and attachment payload are not persisted.

**Next:** Q3.3

### Q3.3 — What gets replaced in message text?

The redaction layer removes or replaces identifiers and sensitive patterns such as emails, phone numbers, links, codes, and personal names. Names are displayed as `[PERSON]` rather than simply deleted so the sentence remains readable.

**Next:** Q3.4

### Q3.4 — Why keep a defanged link placeholder rather than remove every link?

The presence and shape of a link can be a scam signal. Replacing a URL with `[LINK]` or a defanged representation preserves that signal without leaving a clickable tracking URL or an unnecessary destination in the training data.

**Next:** Q3.5

### Q3.5 — Are attachments stored?

No attachment content is retained. The sanitized record may keep a coarse indicator that an attachment existed and, where safe, its extension category. This can be useful evidence without retaining the file.

**Next:** Q3.6

### Q3.6 — Is redaction perfect?

No privacy system should claim perfection. Trustfall uses layered client and server processing, blocks obvious sensitive content, and makes the most useful safety tradeoff it can. Human review remains important before publishing any example.

**Next:** Q3.7

### Q3.7 — What should never appear in a demo, deck, or Devpost submission?

Raw emails, real worker messages, private names, email addresses, phone numbers, API keys, database URLs, Vercel environment variables, or terminal output containing credentials.

**Next:** Q4.1

---

## 4. What is actually stored?

### Q4.1 — What is a `TeracParticipant` record?

It records a participant’s Terac submission ID and workflow state: whether the person is collecting or labeling and whether their task has started or completed.

**Next:** Q4.2

### Q4.2 — What is a `CollectedMessage` record?

It is the sanitized representation of one submitted message. It includes sanitized subject/body/text, source type, initial user belief, limited domain and authentication features, attachment indicators, parser warnings, and a synthetic-fixture flag.

**Next:** Q4.3

### Q4.3 — What is a `MessageLabel` record?

It is one worker’s judgment about one message. It stores risk level, scam type, red flags, recommended action, plain-English warning, confidence, rationale, and timestamp.

**Next:** Q4.4

### Q4.4 — What is a `LabelAssignment` record?

It records which message was assigned to which labeler and at what queue position. It prevents a person from labeling the same message twice and lets Trustfall distinguish assigned work from saved work.

**Next:** Q4.5

### Q4.5 — What is a `QualityFlag`?

It records a caution about data quality, such as an implausibly fast completed label. A flag is evidence for review; it does not silently erase the original data.

**Next:** Q4.6

### Q4.6 — What is an `ExpertAdjudication`?

It is an additive final-target layer for messages that lack enough worker consensus or remain ambiguous. It contains an expert’s final judgment, rationale, reason for adjudication, and a compact PII-free summary of worker-label evidence.

**Next:** Q4.7

### Q4.7 — Does expert adjudication overwrite workers?

No. Worker `MessageLabel` records stay immutable. The final dataset chooses an expert decision when present, but the original judgments remain available for audit.

**Next:** Q5.1

---

## 5. Turning many labels into one target

### Q5.1 — What is a consensus label?

It is the final target derived from multiple independent worker labels on one message. Trustfall uses majority-style choices for risk and scam type, aggregates red flags, and chooses a high-confidence useful action and warning.

**Next:** Q5.2

### Q5.2 — What qualifies for worker consensus?

By default, a message needs at least two independent labels and at least 50% agreement on both risk level and scam type. This is intentionally a modest quality gate for a small pilot, not proof of perfect truth.

**Next:** Q5.3

### Q5.3 — What happens when workers disagree?

The record is marked low-agreement and is not automatically used as worker consensus. It can be excluded or receive an explicit expert adjudication with a documented rationale.

**Next:** Q5.4

### Q5.4 — What happens to gibberish or incomplete submissions?

Trustfall excludes clearly unreviewable records: obvious keyboard mash, extremely corrupted MIME artifacts, and fragments without enough meaningful content. It does not exclude messages merely because they are messy or hard.

**Next:** Q5.5

### Q5.5 — What is final-target precedence?

For every real message, the dataset builder uses:

1. expert adjudication, if present;
2. otherwise worker consensus, if it clears the quality gate;
3. otherwise exclusion.

The exported row records whether its target came from `expert_adjudication` or `worker_consensus`.

**Next:** Q5.6

### Q5.6 — Why keep target provenance?

It lets future reviewers ask how each model example was decided. A dataset that blends consensus and expert choices without provenance is much harder to audit or improve.

**Next:** Q6.1

---

## 6. Dataset snapshots and splits

### Q6.1 — What is a frozen dataset snapshot?

It is a timestamped, immutable export of the messages and final targets that existed at one point in time. Live collection and labeling may keep changing, but a training run must use a stable snapshot.

**Next:** Q6.2

### Q6.2 — Why not train directly from the live database?

If training data changes during or after training, the experiment cannot be reproduced. A frozen snapshot makes it possible to say exactly what the model saw.

**Next:** Q6.3

### Q6.3 — How are messages split?

The final-pilot builder uses a deterministic message-level 70/15/15 train/validation/test split based on a message-ID hash. The same message always lands in the same split for a given logic.

**Next:** Q6.4

### Q6.4 — Why split by message rather than label?

All labels for a message describe the same underlying text. Putting one label in training and another label for the same message in test would leak the answer and make performance look better than it is.

**Next:** Q6.5

### Q6.5 — What is the training split for?

It is the only split used to update Qwen’s LoRA adapter weights.

**Next:** Q6.6

### Q6.6 — What is the validation split for?

It is used for choices such as epochs, learning rate, prompt shape, or adapter settings. It helps avoid choosing settings by looking at the final test result.

**Next:** Q6.7

### Q6.7 — What is the test split for?

It is reserved untouched until the final comparison. It is the fairest available estimate of how the final adapter behaves on unseen messages from the same pilot distribution.

**Next:** Q6.8

### Q6.8 — Is a small test set conclusive?

No. A single-digit test set is a directional pilot signal, not a statistically robust benchmark. Trustfall should report it honestly and improve it as more consensus examples arrive.

**Next:** Q7.1

---

## 7. Qwen, baseline, and LoRA

### Q7.1 — What is Qwen in this project?

`Qwen/Qwen3-0.6B` is the small open language model used as Trustfall’s base model. It receives a sanitized message plus safe metadata and returns structured scam-safety guidance.

**Next:** Q7.2

### Q7.2 — What does the model output?

It is prompted to return one JSON object with `risk_level`, `scam_type`, `red_flags`, `recommended_action`, and `plain_english_warning`.

**Next:** Q7.3

### Q7.3 — What is the baseline?

The baseline is the base Qwen model’s output before Trustfall fine-tunes it. It provides a comparison point for valid JSON, risk classification, scam type, red flags, and advice quality.

**Next:** Q7.4

### Q7.4 — What is LoRA?

LoRA, or Low-Rank Adaptation, trains a small set of adapter weights instead of retraining every weight in the base language model. It is practical for a hackathon-scale dataset and Mac hardware.

**Next:** Q7.5

### Q7.5 — What does Trustfall train on?

Each training example contains a system instruction, sanitized message context, and a final JSON target derived from worker consensus or expert adjudication. No raw email file is used.

**Next:** Q7.6

### Q7.6 — Why does the model receive metadata as well as text?

Signals such as sender domain, reply-to mismatch, link features, authentication summary, and attachment presence can matter even when the visible text alone is ambiguous.

**Next:** Q7.7

### Q7.7 — Where does training run?

Locally on the development Mac, not on Vercel. The training environment uses PyTorch, Transformers, PEFT, and Apple MPS memory-safe settings.

**Next:** Q7.8

### Q7.8 — What does a successful training run create?

It creates a local LoRA adapter directory, tokenizer files, training manifest, immutable dataset snapshot, base-model test predictions, and final comparison JSON. These real-text artifacts are intentionally Git-ignored.

**Next:** Q8.1

---

## 8. Evaluation and honest interpretation

### Q8.1 — How is the final model evaluated?

The base model is first run on the frozen test inputs. After LoRA training on the train split, the adapted model is run on those same untouched test inputs. The outputs are compared against final targets.

**Next:** Q8.2

### Q8.2 — What metrics matter?

Trustfall tracks valid-JSON rate, risk-level exact accuracy, risk-level within-one-level accuracy, scam-type accuracy, and red-flag F1 when applicable.

**Next:** Q8.3

### Q8.3 — Why is valid JSON a meaningful metric?

The product needs structured output that downstream UI code can display safely. A model can be conversationally plausible but operationally unreliable if it does not return parseable fields.

**Next:** Q8.4

### Q8.4 — What did the early pilot show?

The initial small holdout showed better JSON reliability after LoRA adaptation. Exact classification metrics moved directionally, but the holdout was too small to claim meaningful generalization. The deck labels this as a pilot limitation.

**Next:** Q8.5

### Q8.5 — What would make the model claim stronger?

More completed labels, more independently adjudicated messages, a larger untouched test split, repeated or grouped cross-validation for model-setting choices, and qualitative review of unsafe errors.

**Next:** Q8.6

### Q8.6 — What should Trustfall never claim today?

It should not claim production-grade scam detection, broad real-world accuracy, or that a tiny pilot evaluation proves safety. The honest claim is that the workflow works and produces measurable, auditable early evidence.

**Next:** Q9.1

---

## 9. App routes and outputs

### Q9.1 — Where does a collection worker go?

`/terac?mode=collect` opens the Wave 1 workflow. Terac task URLs append a participant submission identifier when the task is launched through the platform.

**Next:** Q9.2

### Q9.2 — Where does a labeler go?

`/terac?mode=label` opens the Wave 2 workflow. In normal use, Terac supplies the task-specific submission identifier. The app assigns that person messages they did not submit.

**Next:** Q9.3

### Q9.3 — What is `/admin/data`?

It is the operational data dashboard: counts, real-message cards, labels, and export actions. It is useful for review, but it should be protected with authentication before being presented as a public admin link.

**Next:** Q9.4

### Q9.4 — What are the export routes?

`/api/export/train` returns JSONL training examples and `/api/export/eval` returns evaluation JSON for messages that meet label requirements. The final-pilot Python builder is the more rigorous route when expert-adjudication provenance and three-way splitting are required.

**Next:** Q9.5

### Q9.5 — What is `/demo`?

It is a synthetic, non-persistent product walkthrough. It shows the collection, redaction, labeling, quality-gate, and model-result story with fake content and aggregate metrics only. It is safe to use in a recorded demo.

**Next:** Q10.1

---

## 10. Presentation, Devpost, and video

### Q10.1 — What should a judge understand in the first 20 seconds?

Trustfall is not merely “an AI that detects scams.” It is a privacy-preserving system for collecting the missing human data needed to make scam guidance more grounded and auditable.

**Next:** Q10.2

### Q10.2 — What does the presentation show?

The PowerPoint tells the full story: problem, workflow, privacy, live operations, label coverage, Qwen baseline, LoRA comparison, architecture, roadmap, and sources. Its charts refresh from a local metrics file.

**Next:** Q10.3

### Q10.3 — How are deck metrics refreshed?

Load the local `DATABASE_URL`, run `scripts/refresh_presentation_metrics.py`, then run `scripts/generate_presentation.cjs`. The deck distinguishes live operational counts from a frozen training snapshot.

**Next:** Q10.4

### Q10.4 — How is the captioned demo video made?

The Playwright recorder visits `/demo`, clicks through the synthetic flow, and injects on-screen captions timed to each scene. It writes a WebM file that can be uploaded to Loom, YouTube, or Drive.

**Next:** Q10.5

### Q10.5 — What links belong on Devpost?

Use the public app as the try-it link, GitHub as the source-code link, and a 2–3 minute Loom or unlisted YouTube walkthrough as the demo link. Do not use the admin dashboard as a public try-it link until authentication is in place.

**Next:** Q11.1

---

## 11. Operating the project safely

### Q11.1 — Where do secrets belong?

In local ignored environment files or Vercel environment variables. They do not belong in Git, screenshots, terminal recordings, decks, prompts, or chat messages.

**Next:** Q11.2

### Q11.2 — What does `TERAC_PILOT_WRITE_ENABLED` control?

It is a deliberate safety gate around Terac write operations. It should normally be `false` and only be temporarily enabled for an intentional create/launch action.

**Next:** Q11.3

### Q11.3 — Why should the admin dashboard be authenticated?

Operational counts and sanitized message review should not be publicly discoverable. Authentication and rate limiting are the most important production hardening work remaining outside the hackathon demonstration.

**Next:** Q11.4

### Q11.4 — Which files should not be committed?

`.env.local`, databases, raw `.eml` files, baseline output, training snapshots with real sanitized text, LoRA artifacts, evaluation records containing text, videos, and PowerPoint lock files.

**Next:** Q11.5

### Q11.5 — What should be committed?

Source code, migrations, schema changes, deterministic scripts, documentation, safe synthetic demo assets, presentation generator code, and a deck that does not include private examples.

**Next:** Q12.1

---

## 12. The current state and the next decisions

### Q12.1 — What has been proven so far?

The full loop works: public app deployment, Terac collection, redaction, persisted labels, partial-label preservation, quality gating, expert final-target support, frozen datasets, baseline inference, LoRA training, evaluation, exports, a deck, and a safe captioned demo.

**Next:** Q12.2

### Q12.2 — What is the main current limitation?

Data volume and label completion. Some workers left assignments incomplete, so the live dataset contains a mix of zero-label, one-label, consensus, and expert-adjudicated messages. This is expected in a pilot but limits statistical confidence.

**Next:** Q12.3

### Q12.3 — What is the best next data-quality move?

Use expert adjudication for one-label and low-agreement cases, preserve worker provenance, then freeze a new final-pilot snapshot. Do not overwrite worker judgments or pretend that all recruitment became completed labels.

**Next:** Q12.4

### Q12.4 — What is the best next ML move?

Run the final-pilot workflow only after the target policy is settled: build the three-way split, baseline the untouched test set, train on train only, use validation for decisions, and evaluate the test set once.

**Next:** Q12.5

### Q12.5 — What is the best next product move?

Protect `/admin/data`, add rate limiting to mutation routes, and turn the model output into an end-user warning experience that clearly states uncertainty and safe next actions.

**Next:** Q12.6

### Q12.6 — What is the best hackathon framing?

“We built the missing feedback loop for scam safety: collect privacy-protected real examples, turn independent human judgment into an auditable target, and measure whether a model becomes more operationally useful.”

**You have reached the end of the tree.**

---

## Fast glossary

| Term | Meaning |
| --- | --- |
| Wave 1 | Participant collection of suspicious and normal messages. |
| Wave 2 | Independent human labeling of redacted messages. |
| Sanitized | Privacy-filtered content safe enough for controlled data use. |
| Consensus | Final target derived from sufficient independent worker agreement. |
| Expert adjudication | Additive documented final judgment for unresolved cases. |
| Frozen snapshot | Versioned dataset used by one reproducible training run. |
| Baseline | Base Qwen performance before Trustfall adaptation. |
| LoRA | Lightweight adapter training instead of full-model retraining. |
| Validation set | Data for training choices; not used to update weights. |
| Test set | Untouched final data used once for evaluation. |
