# Wave 2 Qwen LoRA pipeline

Run this only after Wave 2 has produced at least two completed labels for several real messages. It uses only sanitized, non-synthetic messages, excludes unreadable submissions, and leaves the database unchanged.

```bash
cd "/Users/LukeJun/Desktop/Coding Projects/Hackathon Berkley 2026/trustfall-terac"
python3 -m venv .venv-qwen
.venv-qwen/bin/pip install -r requirements-qwen-training.txt
set -a; source .env.local; set +a
.venv-qwen/bin/python scripts/run_wave2_qwen.py --device mps
```

Before running the pipeline, apply the expert adjudication layer so messages that lack worker consensus still receive a defensible final target (see [final-pilot.md](final-pilot.md)):

```bash
set -a; source .env.local; set +a
.venv-qwen/bin/python scripts/adjudicate_messages.py   # idempotent upsert; prints counts only
```

The pipeline (`run_wave2_qwen.py`) then runs four ordered steps:

1. **build** — freeze a versioned dataset. Final target per message is the expert adjudication when present, otherwise worker consensus when it meets the gate, otherwise the message is excluded.
2. **baseline** — score the base Qwen model on the frozen **test** inputs *before* training.
3. **train** — fine-tune the LoRA adapter on the **train** split only.
4. **evaluate** — run the untouched **test** split once and compare against the baseline.

It creates local-only, Git-ignored artifacts:

- `wave2_training_data/<timestamp>/`: immutable `train.jsonl`, `validation.jsonl`, `test.jsonl`, and `manifest.json` (provenance counts, split counts, small-data limitation).
- `baseline_before_training/<timestamp>/test-baseline.jsonl`: base-model predictions on the test inputs.
- `qwen_lora_artifacts/<timestamp>/`: the Qwen LoRA adapter, not a replacement base model.
- `wave2_evaluation/<timestamp>/comparison.json`: baseline vs. fine-tuned test comparison (valid-JSON rate, risk exact and within-one-level accuracy, scam-type accuracy, red-flag F1).

The split is deterministic at the message level (70/15/15 by a hash of the message id). A message and its labels can never appear in two splits. The default quality gate requires at least two independent labels and at least 50% agreement on both risk level and scam type. Validation is reserved for any training-setting choice; the test split is used exactly once.

For this small pilot, report the resulting comparison as a proof-of-concept. Do not claim production readiness from this data volume alone.
