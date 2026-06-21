#!/usr/bin/env python3
"""One-command, post-Wave-2 Qwen LoRA pipeline. Run locally, never on Vercel."""
import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--min-labels", type=int, default=2)
    parser.add_argument("--min-agreement", type=float, default=0.5)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = Path(__file__).resolve().parent
    data = Path("wave2_training_data") / stamp
    adapter = Path("qwen_lora_artifacts") / stamp
    evaluation = Path("wave2_evaluation") / stamp
    baseline_dir = Path("baseline_before_training") / stamp
    baseline_file = baseline_dir / "test-baseline.jsonl"
    # Order matters: freeze the dataset, score the base model on the untouched
    # test inputs BEFORE training, then train on train only, then evaluate once.
    commands = [
        [sys.executable, str(root / "build_wave2_dataset.py"), "--output-dir", str(data), "--min-labels", str(args.min_labels), "--min-agreement", str(args.min_agreement)],
        [sys.executable, str(root / "run_qwen_baseline.py"), "--dataset-dir", str(data), "--split", "test", "--output-dir", str(baseline_dir), "--device", args.device],
        [sys.executable, str(root / "train_qwen_lora.py"), "--dataset-dir", str(data), "--output-dir", str(adapter), "--device", args.device, "--epochs", str(args.epochs)],
        [sys.executable, str(root / "evaluate_qwen_lora.py"), "--dataset-dir", str(data), "--adapter-dir", str(adapter), "--output-dir", str(evaluation), "--device", args.device, "--baseline-file", str(baseline_file)],
    ]
    for command in commands:
        print("+", " ".join(command))
        subprocess.run(command, check=True)
    print(f"Completed. Adapter: {adapter}; evaluation: {evaluation / 'comparison.json'}")


if __name__ == "__main__":
    main()
