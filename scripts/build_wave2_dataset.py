#!/usr/bin/env python3
"""Freeze an immutable final-pilot dataset.

Final-target precedence for each real, sanitized message:
  1. expert adjudication, when an ExpertAdjudication row exists;
  2. otherwise independent-worker consensus, when it meets the quality gate;
  3. otherwise the message is excluded.

Every exported row and the manifest record provenance
(`expert_adjudication` or `worker_consensus`). The dataset is split by message
(never by individual label) into a deterministic 70/15/15 train/validation/test
split. The test split is reserved untouched for a single final evaluation.
"""
import argparse
import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from qwen_training_common import (
    SYSTEM, agreement, consensus, is_reviewable, model_input, parse_flags, split_bucket,
)


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


def load_adjudications(url):
    query = '''SELECT "messageId", "candidateReason", "riskLevel", "scamType", "redFlags",
      "recommendedAction", "plainEnglishWarning", "rationale", "adjudicatorId"
      FROM "ExpertAdjudication"'''
    if url.startswith("file:"):
        connection = sqlite3.connect(url.removeprefix("file:"))
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(query)]
    else:
        import psycopg
        with psycopg.connect(url) as connection, connection.cursor() as cursor:
            cursor.execute(query)
            names = [column.name for column in cursor.description]
            rows = [dict(zip(names, row)) for row in cursor.fetchall()]
    return {row["messageId"]: row for row in rows}


def expert_target(adjudication):
    return {
        "risk_level": adjudication["riskLevel"],
        "scam_type": adjudication["scamType"],
        "red_flags": parse_flags(adjudication["redFlags"]),
        "recommended_action": (adjudication["recommendedAction"] or "").strip(),
        "plain_english_warning": (adjudication["plainEnglishWarning"] or "").strip(),
    }


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
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
    adjudications = load_adjudications(args.database_url)

    included, rejected, provenance = [], Counter(), Counter()
    for message in grouped.values():
        labels = message.get("labels", [])
        reviewable = is_reviewable(message["sanitizedText"])
        adjudication = adjudications.get(message["id"])
        if not reviewable:
            rejected["not_reviewable"] += 1
            continue
        if adjudication:
            target, source = expert_target(adjudication), "expert_adjudication"
            extra = {"candidate_reason": adjudication["candidateReason"], "adjudicator": adjudication["adjudicatorId"], "label_count": len(labels)}
        elif len(labels) < args.min_labels:
            rejected["not_enough_labels"] += 1
            continue
        elif min(agreement(labels, "riskLevel"), agreement(labels, "scamType")) < args.min_agreement:
            rejected["low_agreement"] += 1
            continue
        else:
            target, source = consensus(labels), "worker_consensus"
            extra = {"label_count": len(labels), "risk_agreement": agreement(labels, "riskLevel"),
                     "scam_type_agreement": agreement(labels, "scamType")}
        provenance[source] += 1
        included.append({
            "id": message["id"], "provenance": source, "input": model_input(message),
            "labels": target, "split": split_bucket(message["id"]), **extra,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": model_input(message)},
                {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
            ],
        })

    if len(included) < 5:
        raise SystemExit(f"Only {len(included)} messages meet the final-target gate; gather more labels or adjudications.")

    splits = {name: [row for row in included if row["split"] == name] for name in ("train", "validation", "test")}
    # A reserved test split must exist even on a tiny dataset; borrow the
    # deterministically last eligible message if the hash left test empty.
    if not splits["test"]:
        donor = sorted(included, key=lambda row: row["id"])[-1]
        splits[donor["split"]] = [row for row in splits[donor["split"]] if row["id"] != donor["id"]]
        donor["split"] = "test"
        splits["test"] = [donor]

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "train.jsonl", splits["train"])
    write_jsonl(output / "validation.jsonl", splits["validation"])
    write_jsonl(output / "test.jsonl", splits["test"])

    small_data = len(splits["test"]) < 10
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "real sanitized pilot messages only (isSyntheticTestFixture=false)",
        "final_target_precedence": ["expert_adjudication", "worker_consensus", "exclude"],
        "quality_gate": {"min_labels": args.min_labels, "min_agreement": args.min_agreement},
        "eligible_messages": len(included),
        "provenance_counts": dict(provenance),
        "split": "deterministic, message-level 70/15/15 train/validation/test (hash of message id)",
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "split_provenance": {
            name: dict(Counter(row["provenance"] for row in rows)) for name, rows in splits.items()
        },
        "excluded": dict(rejected),
        "test_split_usage": "reserved untouched; used once for the final evaluation only",
        "small_data_limitation": (
            f"The frozen test split holds only {len(splits['test'])} message(s); reported test metrics are "
            "directional, not statistically robust, and should be read as a pilot signal rather than a benchmark."
            if small_data else
            f"The frozen test split holds {len(splits['test'])} messages."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
