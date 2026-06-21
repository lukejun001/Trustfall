#!/usr/bin/env python3
"""Apply expert adjudications as an additive final-target layer.

Reads the expert judgments in scripts/expert_adjudications.json and upserts one
ExpertAdjudication row per real, sanitized candidate message that lacks
independent-worker consensus (single label, no labels, low agreement) or is
otherwise ambiguous. Worker MessageLabel rows are never modified.

Operates only on sanitized data. Prints a count summary only -- never message
bodies, worker free-text, addresses, or secrets.
"""
import argparse
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path

from qwen_training_common import agreement, is_reviewable, parse_flags

# Mirror of lib/constants.ts controlled vocabularies for validation.
RISKS = {"safe", "low", "medium", "high", "unsure"}
SCAM_TYPES = {
    "not_scam", "delivery_phishing", "bank_phishing", "fake_job", "fake_check",
    "crypto", "romance", "marketplace", "tech_support", "government_impersonation",
    "account_takeover", "payment_app", "other", "unsure",
}
RED_FLAGS = {
    "urgent_language", "suspicious_link", "asks_for_payment", "asks_for_password_or_code",
    "too_good_to_be_true", "impersonates_trusted_brand", "weird_sender_or_domain",
    "threatens_consequences", "asks_to_move_off_platform", "requests_personal_info",
    "unusual_payment_method", "poor_grammar_or_formatting", "none",
}
ADJUDICATOR = "claude-code-expert"
MIN_LABELS = 2
MIN_AGREEMENT = 0.5


def load_messages(url):
    """Return {message_id: {sanitizedText, labels:[{riskLevel,scamType,redFlags,confidence}]}}."""
    query = '''SELECT m.id, m."sanitizedText", l."riskLevel", l."scamType", l."redFlags", l.confidence
      FROM "CollectedMessage" m LEFT JOIN "MessageLabel" l ON l."messageId" = m.id
      WHERE m."isSyntheticTestFixture" = ?'''
    if url.startswith("file:"):
        connection = sqlite3.connect(url.removeprefix("file:"))
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(query.replace("?", "0"))]
    else:
        import psycopg
        with psycopg.connect(url) as connection, connection.cursor() as cursor:
            cursor.execute(query.replace("?", "%s"), (False,))
            names = [column.name for column in cursor.description]
            rows = [dict(zip(names, row)) for row in cursor.fetchall()]
    grouped = {}
    for row in rows:
        message = grouped.setdefault(row["id"], {"sanitizedText": row["sanitizedText"], "labels": []})
        if row.get("riskLevel"):
            message["labels"].append({
                "riskLevel": row["riskLevel"], "scamType": row["scamType"],
                "redFlags": row["redFlags"], "confidence": row["confidence"],
            })
    return grouped


def candidate_reason(message):
    """Return the consensus-gate reason a message needs adjudication, or None."""
    if not is_reviewable(message["sanitizedText"]):
        return None  # excluded as not reviewable; never adjudicated
    labels = message["labels"]
    if len(labels) == 0:
        return "no_labels"
    if len(labels) == 1:
        return "single_label"
    if min(agreement(labels, "riskLevel"), agreement(labels, "scamType")) < MIN_AGREEMENT:
        return "low_agreement"
    return None  # already meets worker-consensus gate


def evidence_snapshot(labels):
    """Compact, PII-free record of the worker-label evidence considered."""
    return {
        "worker_label_count": len(labels),
        "risk_levels": dict(Counter(label["riskLevel"] for label in labels)),
        "scam_types": dict(Counter(label["scamType"] for label in labels)),
        "red_flag_frequency": dict(Counter(
            flag for label in labels for flag in parse_flags(label.get("redFlags"))
        )),
        "confidences": [label.get("confidence") for label in labels],
    }


def validate(entry):
    problems = []
    if entry["risk_level"] not in RISKS:
        problems.append(f"risk_level={entry['risk_level']}")
    if entry["scam_type"] not in SCAM_TYPES:
        problems.append(f"scam_type={entry['scam_type']}")
    bad_flags = [flag for flag in entry["red_flags"] if flag not in RED_FLAGS]
    if bad_flags:
        problems.append(f"red_flags={bad_flags}")
    if not entry["red_flags"]:
        problems.append("red_flags is empty")
    return problems


def upsert(url, rows):
    columns = ("id", "messageId", "adjudicatorId", "candidateReason", "riskLevel", "scamType",
               "redFlags", "recommendedAction", "plainEnglishWarning", "rationale", "evidence")
    update = ", ".join(f'"{c}" = excluded."{c}"' for c in columns if c not in ("id", "messageId"))
    if url.startswith("file:"):
        connection = sqlite3.connect(url.removeprefix("file:"))
        placeholders = ", ".join("?" for _ in columns)
        sql = (f'INSERT INTO "ExpertAdjudication" ({", ".join(chr(34)+c+chr(34) for c in columns)}) '
               f'VALUES ({placeholders}) ON CONFLICT("messageId") DO UPDATE SET {update}, '
               f'"adjudicatedAt" = CURRENT_TIMESTAMP')
        connection.executemany(sql, rows)
        connection.commit()
        return
    import psycopg
    placeholders = ", ".join("%s" for _ in columns)
    sql = (f'INSERT INTO "ExpertAdjudication" ({", ".join(chr(34)+c+chr(34) for c in columns)}) '
           f'VALUES ({placeholders}) ON CONFLICT ("messageId") DO UPDATE SET {update}, '
           f'"adjudicatedAt" = CURRENT_TIMESTAMP')
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.executemany(sql, rows)
        connection.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--adjudications", default=str(Path(__file__).resolve().parent / "expert_adjudications.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("Set DATABASE_URL or pass --database-url.")

    document = json.loads(Path(args.adjudications).read_text(encoding="utf-8"))
    adjudications = {entry["message_id"]: entry for entry in document["adjudications"]}
    excluded_ids = {entry["message_id"] for entry in document.get("_excluded", [])}
    messages = load_messages(args.database_url)

    candidates = {mid: candidate_reason(m) for mid, m in messages.items()}
    candidate_ids = {mid for mid, reason in candidates.items() if reason}

    rows, summary = [], Counter()
    for message_id, entry in adjudications.items():
        if message_id not in messages:
            summary["skipped_message_absent"] += 1
            continue
        problems = validate(entry)
        if problems:
            raise SystemExit(f"Invalid adjudication for {message_id}: {problems}")
        if candidates.get(message_id) is None:
            # Message now meets worker consensus or is not reviewable; keep the
            # record but flag it so the count summary stays honest.
            summary["skipped_no_longer_candidate"] += 1
            continue
        evidence = evidence_snapshot(messages[message_id]["labels"])
        rows.append((
            f"expadj_{message_id}", message_id, ADJUDICATOR, candidates[message_id],
            entry["risk_level"], entry["scam_type"], json.dumps(entry["red_flags"]),
            entry["recommended_action"], entry["plain_english_warning"], entry["rationale"],
            json.dumps(evidence),
        ))
        summary[f"adjudicated_{candidates[message_id]}"] += 1

    adjudicated_ids = {row[1] for row in rows}
    pending = candidate_ids - adjudicated_ids - excluded_ids
    intentionally_excluded = candidate_ids & excluded_ids

    if not args.dry_run and rows:
        upsert(args.database_url, rows)

    report = {
        "real_messages": len(messages),
        "adjudication_candidates": len(candidate_ids),
        "adjudicated_total": len(rows),
        "by_reason": {key.removeprefix("adjudicated_"): value for key, value in summary.items() if key.startswith("adjudicated_")},
        "intentionally_excluded": len(intentionally_excluded),
        "candidates_without_adjudication": len(pending),
        "skipped_message_absent": summary.get("skipped_message_absent", 0),
        "skipped_no_longer_candidate": summary.get("skipped_no_longer_candidate", 0),
        "dry_run": args.dry_run,
    }
    print(json.dumps(report, indent=2))
    if pending:
        print(f"NOTE: {len(pending)} reviewable candidate(s) have no expert adjudication yet.")


if __name__ == "__main__":
    main()
