#!/usr/bin/env python3
"""Compare the Qwen baseline and LoRA adapter on the frozen Wave 2 holdout."""
import argparse
import json
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from qwen_training_common import MODEL, SYSTEM, parse_model_json


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pick_device(name):
    if name == "auto":
        return "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    return name


def generate(model, tokenizer, row, device):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": row["input"]}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    inputs = tokenizer([prompt], return_tensors="pt").to(device)
    output = model.generate(**inputs, max_new_tokens=300, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()


def metrics(rows, prediction_key):
    parsed = [row for row in rows if row.get(prediction_key)]
    total = len(rows)
    risk = sum(row[prediction_key].get("risk_level") == row["labels"]["risk_level"] for row in parsed)
    scam = sum(row[prediction_key].get("scam_type") == row["labels"]["scam_type"] for row in parsed)
    return {"examples": total, "valid_json_rate": len(parsed) / total if total else 0, "risk_exact_accuracy": risk / total if total else 0, "scam_type_exact_accuracy": scam / total if total else 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--adapter-dir", required=True)
    parser.add_argument("--baseline-file")
    parser.add_argument("--output-dir", default="wave2_evaluation/latest")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    args = parser.parse_args()
    device = pick_device(args.device)
    rows = load_jsonl(Path(args.dataset_dir) / "eval.jsonl")
    if not rows:
        raise SystemExit("The frozen evaluation split is empty.")
    baseline = {}
    if args.baseline_file:
        baseline = {row["message_id"]: row.get("prediction") for row in load_jsonl(Path(args.baseline_file))}
    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.float32 if device == "cpu" else torch.float16
    base = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device)
    model = PeftModel.from_pretrained(base, args.adapter_dir).to(device)
    model.eval()
    for row in rows:
        raw = generate(model, tokenizer, row, device)
        row["fine_tuned_raw_output"] = raw
        row["fine_tuned_prediction"] = parse_model_json(raw)
        row["baseline_prediction"] = baseline.get(row["id"])
    report = {"baseline": metrics(rows, "baseline_prediction") if baseline else None, "fine_tuned": metrics(rows, "fine_tuned_prediction"), "examples": rows}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"baseline": report["baseline"], "fine_tuned": report["fine_tuned"]}, indent=2))


if __name__ == "__main__":
    main()
