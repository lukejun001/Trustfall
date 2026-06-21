#!/usr/bin/env python3
"""Fine-tune a local Qwen LoRA adapter on an immutable Wave 2 consensus dataset."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import torch
from peft import LoraConfig, TaskType, get_peft_model
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer

from qwen_training_common import MODEL


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def device_config(name):
    if name == "auto":
        name = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    if name == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is unavailable.")
    if name == "mps" and not torch.backends.mps.is_available():
        raise SystemExit("MPS was requested but is unavailable.")
    return name, torch.float32 if name == "cpu" else torch.float16


def tokenized_row(row, tokenizer, max_length):
    prompt = tokenizer.apply_chat_template(row["messages"][:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False, enable_thinking=False)
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    full_ids = tokenizer(full, add_special_tokens=False, truncation=True, max_length=max_length)["input_ids"]
    labels = full_ids.copy()
    labels[: min(len(prompt_ids), len(labels))] = [-100] * min(len(prompt_ids), len(labels))
    return {"input_ids": full_ids, "labels": labels}


def collate(batch, pad_id):
    maximum = max(len(item["input_ids"]) for item in batch)
    input_ids, attention_mask, labels = [], [], []
    for item in batch:
        padding = maximum - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [pad_id] * padding)
        attention_mask.append([1] * len(item["input_ids"]) + [0] * padding)
        labels.append(item["labels"] + [-100] * padding)
    return {"input_ids": torch.tensor(input_ids), "attention_mask": torch.tensor(attention_mask), "labels": torch.tensor(labels)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-dir", default="qwen_lora_artifacts/latest")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=1536)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    dataset = Path(args.dataset_dir)
    rows = load_rows(dataset / "train.jsonl")
    if len(rows) < 4:
        raise SystemExit("Training split is too small; need at least four consensus messages.")
    device, dtype = device_config(args.device)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dtype)
    model.config.use_cache = False
    model.to(device)
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, config)
    items = [tokenized_row(row, tokenizer, args.max_length) for row in rows]
    loader = DataLoader(items, batch_size=1, shuffle=True, collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id))
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=args.learning_rate)
    model.train()
    losses = []
    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            loss = model(**batch).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            epoch_loss += loss.item()
        average = epoch_loss / max(len(loader), 1)
        losses.append(average)
        print(f"epoch {epoch + 1}/{args.epochs}: loss={average:.4f}")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    (output / "training_manifest.json").write_text(json.dumps({
        "base_model": args.model, "created_at": datetime.now(timezone.utc).isoformat(), "device": device,
        "train_messages": len(rows), "epochs": args.epochs, "learning_rate": args.learning_rate,
        "final_loss": losses[-1], "epoch_losses": losses, "dataset_dir": str(dataset),
        "method": "LoRA; source messages unchanged; adapter only",
    }, indent=2), encoding="utf-8")
    print(f"Saved LoRA adapter to {output}")


if __name__ == "__main__":
    main()
