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
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    response_ids = tokenizer(row["messages"][-1]["content"] + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
    # Keep the complete target JSON. When a source email is long, discard the
    # oldest prompt tokens rather than silently masking the entire answer.
    response_ids = response_ids[:max_length]
    prompt_budget = max(0, max_length - len(response_ids))
    prompt_ids = prompt_ids[-prompt_budget:] if prompt_budget else []
    return {"input_ids": prompt_ids + response_ids, "labels": [-100] * len(prompt_ids) + response_ids}


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
    parser.add_argument("--max-length", type=int, default=512)
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
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype)
    model.config.use_cache = False
    # This is essential for a 0.6B model on an 18 GB Apple unified-memory pool.
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
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
