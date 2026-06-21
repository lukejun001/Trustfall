#!/usr/bin/env python3
"""Refresh editable Trustfall presentation metrics from the local production connection."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import psycopg


def latest_json(directory, name):
    files = sorted(Path(directory).glob(f"*/{name}"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def main():
    output = Path("presentation/trustfall-metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("Set DATABASE_URL before refreshing presentation metrics.")
    with psycopg.connect(os.environ["DATABASE_URL"]) as connection, connection.cursor() as cursor:
        cursor.execute('SELECT count(*) FROM "CollectedMessage" WHERE "isSyntheticTestFixture" = false')
        real_messages = cursor.fetchone()[0]
        cursor.execute('SELECT count(*) FROM "MessageLabel"')
        saved_labels = cursor.fetchone()[0]
        cursor.execute('SELECT count(*) FROM "LabelAssignment"')
        assigned_labels = cursor.fetchone()[0]
        cursor.execute('SELECT count(*) FROM "TeracParticipant" WHERE wave = %s AND status = %s', ("label", "label_completed"))
        completed_labelers = cursor.fetchone()[0]
        cursor.execute('''SELECT count(l.id) AS label_count FROM "CollectedMessage" m
          LEFT JOIN "MessageLabel" l ON l."messageId" = m.id
          WHERE m."isSyntheticTestFixture" = false GROUP BY m.id''')
        distribution = Counter(row[0] for row in cursor.fetchall())
    training = latest_json("wave2_training_data", "manifest.json") or {}
    comparison = latest_json("wave2_evaluation", "comparison.json") or {}
    metrics = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "real_messages": real_messages,
        "saved_labels": saved_labels,
        "assigned_labels": assigned_labels,
        "planned_labelers": assigned_labels // 8,
        "completed_labelers": completed_labelers,
        "labels_per_message": {str(key): distribution[key] for key in sorted(distribution)},
        "training_snapshot": training,
        "model_comparison": {key: value for key, value in comparison.items() if key != "examples"},
    }
    output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
