# Wave 2 Qwen LoRA pipeline

Run this only after Wave 2 has produced at least two completed labels for several real messages. It uses only sanitized, non-synthetic messages, excludes unreadable submissions, and leaves the database unchanged.

```bash
cd "/Users/LukeJun/Desktop/Coding Projects/Hackathon Berkley 2026/trustfall-terac"
python3 -m venv .venv-qwen
.venv-qwen/bin/pip install -r requirements-qwen-training.txt
set -a; source .env.local; set +a
.venv-qwen/bin/python scripts/run_wave2_qwen.py --device mps
```

The pipeline creates local-only, Git-ignored artifacts:

- `wave2_training_data/<timestamp>/`: immutable consensus train/eval files and quality manifest.
- `qwen_lora_artifacts/<timestamp>/`: the Qwen LoRA adapter, not a replacement base model.
- `wave2_evaluation/<timestamp>/comparison.json`: baseline vs. fine-tuned holdout comparison.

The holdout split is deterministic at the message level. An email and its labels can never appear in both training and evaluation. The default quality gate requires at least two independent labels and at least 50% agreement on both risk level and scam type.

For this small pilot, report the resulting comparison as a proof-of-concept. Do not claim production readiness from this data volume alone.
