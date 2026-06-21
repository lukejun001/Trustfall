#!/usr/bin/env python3
"""Refresh editable Trustfall presentation metrics from the local production connection.

Separates *live operational* counts (queried fresh from production) from the
*frozen final-pilot snapshot* (read from the immutable training manifest and the
one-time evaluation comparison), and surfaces worker-consensus vs.
expert-adjudicated provenance plus the small-data limitation.
"""
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
        cursor.execute('SELECT count(*) FROM "ExpertAdjudication"')
        expert_adjudications = cursor.fetchone()[0]
        cursor.execute('SELECT count(*) FROM "TeracParticipant" WHERE wave = %s AND status = %s', ("label", "label_completed"))
        completed_labelers = cursor.fetchone()[0]
        cursor.execute('''SELECT count(l.id) AS label_count FROM "CollectedMessage" m
          LEFT JOIN "MessageLabel" l ON l."messageId" = m.id
          WHERE m."isSyntheticTestFixture" = false GROUP BY m.id''')
        distribution = Counter(row[0] for row in cursor.fetchall())
    training = latest_json("wave2_training_data", "manifest.json") or {}
    comparison = latest_json("wave2_evaluation", "comparison.json") or {}
    provenance = training.get("provenance_counts", {})
    split_counts = training.get("split_counts", {})
    metrics = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        # --- Live operational counts (change as the pilot runs) ---
        "live_operational": {
            "real_messages": real_messages,
            "saved_labels": saved_labels,
            "assigned_labels": assigned_labels,
            "planned_labelers": assigned_labels // 8,
            "completed_labelers": completed_labelers,
            "expert_adjudications": expert_adjudications,
            "labels_per_message": {str(key): distribution[key] for key in sorted(distribution)},
        },
        # --- Frozen final-pilot snapshot (immutable once built) ---
        "frozen_snapshot": {
            "created_at": training.get("created_at"),
            "eligible_messages": training.get("eligible_messages"),
            "worker_consensus": provenance.get("worker_consensus"),
            "expert_adjudication": provenance.get("expert_adjudication"),
            "train_messages": split_counts.get("train"),
            "validation_messages": split_counts.get("validation"),
            "test_messages": split_counts.get("test"),
            "excluded": training.get("excluded", {}),
            "small_data_limitation": training.get("small_data_limitation"),
        },
        "model_comparison": {key: value for key, value in comparison.items() if key != "examples"},
        # --- Backward-compatible flat keys for the existing deck generator ---
        "real_messages": real_messages,
        "saved_labels": saved_labels,
        "assigned_labels": assigned_labels,
        "planned_labelers": assigned_labels // 8,
        "completed_labelers": completed_labelers,
        "labels_per_message": {str(key): distribution[key] for key in sorted(distribution)},
        "training_snapshot": training,
    }
    output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
