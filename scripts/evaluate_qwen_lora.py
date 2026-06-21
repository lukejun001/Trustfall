#!/usr/bin/env python3
"""Final, one-time comparison of the base Qwen baseline and the LoRA adapter.

Runs only on the frozen, untouched test split. The base-model baseline is
generated on the exact same test inputs (preferably loaded from a baseline file
produced before training; otherwise regenerated here from the base weights).
Reports valid-JSON rate, risk-level exact and within-one-level accuracy,
scam-type accuracy, and red-flag F1.
"""
import argparse
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from qwen_training_common import MODEL, SYSTEM, parse_model_json

RISK_ORDER = {"safe": 0, "low": 1, "medium": 2, "high": 3}


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def pick_device(name):
    if name == "auto":
        return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    return name


def generate(model, tokenizer, text, device):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    inputs = tokenizer([prompt], return_tensors="pt").to(device)
    output = model.generate(**inputs, max_new_tokens=300, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


def within_one(pred, true):
    if pred == true:
        return True
    if pred in RISK_ORDER and true in RISK_ORDER:
        return abs(RISK_ORDER[pred] - RISK_ORDER[true]) <= 1
    return False  # "unsure" is off-scale: only an exact match counts


def flag_set(value):
    flags = value if isinstance(value, list) else []
    return {str(flag).strip() for flag in flags if str(flag).strip() and str(flag).strip() != "none"}


def metrics(rows, prediction_key):
    total = len(rows)
    parsed = [row for row in rows if row.get(prediction_key)]
    risk_exact = risk_within = scam_exact = 0
    tp = fp = fn = 0
    for row in parsed:
        prediction, target = row[prediction_key], row["labels"]
        if prediction.get("risk_level") == target["risk_level"]:
            risk_exact += 1
        if within_one(prediction.get("risk_level"), target["risk_level"]):
            risk_within += 1
        if prediction.get("scam_type") == target["scam_type"]:
            scam_exact += 1
        predicted_flags, target_flags = flag_set(prediction.get("red_flags")), flag_set(target.get("red_flags"))
        tp += len(predicted_flags & target_flags)
        fp += len(predicted_flags - target_flags)
        fn += len(target_flags - predicted_flags)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "examples": total,
        "valid_json_rate": len(parsed) / total if total else 0,
        "risk_exact_accuracy": risk_exact / total if total else 0,
        "risk_within_one_accuracy": risk_within / total if total else 0,
        "scam_type_exact_accuracy": scam_exact / total if total else 0,
        "red_flag_f1": f1, "red_flag_precision": precision, "red_flag_recall": recall,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--adapter-dir", required=True)
    parser.add_argument("--baseline-file", help="Base predictions produced before training, keyed by message id.")
    parser.add_argument("--output-dir", default="wave2_evaluation/latest")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    args = parser.parse_args()
    device = pick_device(args.device)
    rows = load_jsonl(Path(args.dataset_dir) / "test.jsonl")
    if not rows:
        raise SystemExit("The frozen test split is empty.")

    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.float32 if device == "cpu" else torch.float16
    base = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device)
    base.eval()

    # Baseline: prefer the pre-training baseline file; otherwise generate from
    # the untrained base weights on the identical test inputs.
    pre_baseline = {}
    if args.baseline_file and Path(args.baseline_file).exists():
        pre_baseline = {row["message_id"]: row.get("prediction") for row in load_jsonl(args.baseline_file)}
    baseline_source = "pre_training_baseline_file" if pre_baseline else "base_weights_on_test_inputs"
    for row in rows:
        if row["id"] in pre_baseline:
            row["baseline_prediction"] = pre_baseline[row["id"]]
        else:
            raw = generate(base, tokenizer, row["input"], device)
            row["baseline_raw_output"] = raw
            row["baseline_prediction"] = parse_model_json(raw)

    model = PeftModel.from_pretrained(base, args.adapter_dir).to(device)
    model.eval()
    for row in rows:
        raw = generate(model, tokenizer, row["input"], device)
        row["fine_tuned_raw_output"] = raw
        row["fine_tuned_prediction"] = parse_model_json(raw)

    report = {
        "test_examples": len(rows),
        "baseline_source": baseline_source,
        "baseline": metrics(rows, "baseline_prediction"),
        "fine_tuned": metrics(rows, "fine_tuned_prediction"),
        "test_provenance": {provenance: sum(1 for row in rows if row.get("provenance") == provenance)
                            for provenance in {row.get("provenance") for row in rows}},
        "examples": rows,
    }
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("test_examples", "baseline_source", "baseline", "fine_tuned")}, indent=2))


if __name__ == "__main__":
    main()
