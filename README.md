# Trustfall Terac workflow

Trustfall collects privacy-protected, real human judgments about suspicious and legitimate messages during a Terac event. It is a small Next.js App Router project using Prisma and SQLite locally.

> **Only Terac-collected labels should be used for training.** Do not add public datasets, Kaggle, Hugging Face, or AI-generated labels to the training set.

## Run locally

```bash
npm install
cp .env.example .env
npx prisma migrate dev --name init
npm run dev
```

Visit `http://localhost:3000/terac?mode=collect&teracSubmissionId=test123` for **Trustfall Wave 1: Message Collection**. Workers submit one suspicious and one normal message, review browser-redacted previews, and return directly to Terac—no labeling is part of this wave. Wave 2 labeling remains separate and requires messages from other participants.

Wave 1 defaults to a local `.eml` upload: the browser parses it, strips attachments and raw headers, and sends only the worker-approved sanitized preview to the API. Use the visible paste-text fallback for SMS, DMs, marketplace posts, and other non-email messages. Run `npm run test:sanitization` to check `.eml` parsing and redaction behavior.

Visit `http://localhost:3000/terac?mode=label&teracSubmissionId=test-label-1` for **Trustfall Wave 2: Message Labeling**. Each worker receives `LABELS_PER_PARTICIPANT` redacted messages (8 by default), prioritized by fewest existing labels. Labeling cannot begin until enough Wave 1 messages exist.

The admin overview is at `/admin/data`. Downloadable exports are at `/api/export/train` and `/api/export/eval`; only messages with two or more human labels are included. The deterministic ID hash assigns 80% to train and 20% to holdout evaluation.

## Privacy model

Raw message text is only held in the browser while the user is filling the form. Before any write, the server replaces links, email addresses, phone numbers, and 4+ digit codes. It never stores unredacted input. Participants must also attest that they removed private information and have a right to share the message.

## Terac callback

Set `TERAC_CALLBACK_BASE_URL` to Terac’s completion callback origin or URL. `/api/terac/callback?teracSubmissionId=…` then redirects there with `teracSubmissionId` and `result=completed`. Without it, the app redirects to the local completion screen.

## Terac Wave 1 pilot API

Set `TERAC_API_KEY` only in `.env` or your deployment secret store; never expose it to the browser. `GET /api/terac/pilot` lists projects (read-only). `POST /api/terac/pilot` supports `create_project` and `create_wave1_draft`, but only after setting `TERAC_PILOT_WRITE_ENABLED=true`. The integration deliberately does not expose Terac's launch endpoint: creating a draft is safe for review, while launch begins recruitment and may incur cost.

## Vercel

Set `DATABASE_URL` to a production-compatible Prisma database (SQLite is for local development; use a hosted relational database adapter before production deployment) and `TERAC_CALLBACK_BASE_URL` in Vercel project settings. Run `prisma generate` during build if your deployment environment does not do it automatically.
