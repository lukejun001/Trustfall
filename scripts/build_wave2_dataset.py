#!/usr/bin/env python3
"""Build an immutable consensus dataset after Wave 2 labels are complete."""
import argparse
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from qwen_training_common import SYSTEM, agreement, consensus, is_reviewable, is_train_id, model_input


def load_rows(url):
    query = '''SELECT m.id, m."sanitizedText", m."sanitizedSubject", m."sanitizedBody", m.source,
      m."fromDomain", m."replyToDomain", m."returnPathDomain", m."linkFeatures", m."authSummary",
      m."hasAttachments", m."createdAt", l."riskLevel", l."scamType", l."redFlags",
      l."recommendedAction", l."plainEnglishWarning", l.confidence, l."createdAt" AS "labelCreatedAt"
      FROM "CollectedMessage" m LEFT JOIN "MessageLabel" l ON l."messageId" = m.id
      WHERE m."isSyntheticTestFixture" = ? ORDER BY m."createdAt" ASC, l."createdAt" ASC'''
    if url.startswith("file:"):
        connection = sqlite3.connect(url.removeprefix("file:"))
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(query.replace("?", "0"))]
    import psycopg
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute(query.replace("?", "%s"), (False,))
        names = [column.name for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def write_jsonl(path, rows):
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--output-dir", default="wave2_training_data/latest")
    parser.add_argument("--min-labels", type=int, default=2)
    parser.add_argument("--min-agreement", type=float, default=0.5)
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("Set DATABASE_URL or pass --database-url.")
    if args.min_labels < 2:
        raise SystemExit("--min-labels must be at least 2 for independent-label consensus.")

    grouped = {}
    for row in load_rows(args.database_url):
        message = grouped.setdefault(row["id"], {key: row[key] for key in row if key not in {
            "riskLevel", "scamType", "redFlags", "recommendedAction", "plainEnglishWarning", "confidence", "labelCreatedAt"
        }})
        if row.get("riskLevel"):
            message.setdefault("labels", []).append({
                "riskLevel": row["riskLevel"], "scamType": row["scamType"], "redFlags": row["redFlags"],
                "recommendedAction": row["recommendedAction"], "plainEnglishWarning": row["plainEnglishWarning"],
                "confidence": row["confidence"], "createdAt": row["labelCreatedAt"],
            })

    included, rejected = [], Counter()
    for message in grouped.values():
        labels = message.get("labels", [])
        if not is_reviewable(message["sanitizedText"]):
            rejected["not_reviewable"] += 1
        elif len(labels) < args.min_labels:
            rejected["not_enough_labels"] += 1
        elif min(agreement(labels, "riskLevel"), agreement(labels, "scamType")) < args.min_agreement:
            rejected["low_agreement"] += 1
        else:
            target = consensus(labels)
            included.append({
                "id": message["id"],
                "input": model_input(message),
                "labels": target,
                "label_count": len(labels),
                "risk_agreement": agreement(labels, "riskLevel"),
                "scam_type_agreement": agreement(labels, "scamType"),
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": model_input(message)},
                    {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
                ],
            })

    if len(included) < 5:
        raise SystemExit(f"Only {len(included)} messages meet the quality gate; wait for Wave 2 labels before training.")
    train = [row for row in included if is_train_id(row["id"])]
    evaluation = [row for row in included if not is_train_id(row["id"])]
    if not evaluation:
        evaluation = [train.pop()]
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "train.jsonl", train)
    write_jsonl(output / "eval.jsonl", evaluation)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(), "source": "real sanitized Wave 1 messages only",
        "quality_gate": {"min_labels": args.min_labels, "min_agreement": args.min_agreement},
        "eligible_messages": len(included), "train_messages": len(train), "eval_messages": len(evaluation),
        "excluded": dict(rejected), "split": "deterministic, message-level 80/20 split",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
