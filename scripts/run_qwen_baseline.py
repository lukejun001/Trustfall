#!/usr/bin/env python3
"""Run an immutable pre-training Qwen baseline over real sanitized Wave 1 messages."""
import argparse, json, os, re, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

MODEL = "Qwen/Qwen3-0.6B"
SYSTEM = """You are Trustfall, a scam detection assistant. Analyze only the sanitized message supplied. Return one JSON object with: risk_level (safe|low|medium|high|unsure), scam_type, red_flags (array), recommended_action, plain_english_warning. Do not invent private information. Be cautious and clear."""

def load_rows(url: str):
    query = '''SELECT id, "sanitizedText", "sanitizedSubject", "sanitizedBody", source,
      "fromDomain", "replyToDomain", "returnPathDomain", "linkFeatures", "authSummary",
      "hasAttachments", "attachmentExtensions", "createdAt"
      FROM "CollectedMessage" WHERE "isSyntheticTestFixture" = ? ORDER BY "createdAt" ASC'''
    if url.startswith("file:"):
        path = url.removeprefix("file:")
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query.replace('?', '0'))]
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Postgres requires `pip install psycopg[binary]`.") from exc
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(query.replace('?', '%s'), (False,))
        names = [desc.name for desc in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]

def user_content(row):
    if row.get("_prebuilt_input") is not None:
        return row["_prebuilt_input"]
    values = [
        ("Subject", row.get("sanitizedSubject")), ("From domain", row.get("fromDomain")),
        ("Reply-to domain", row.get("replyToDomain")), ("Return-path domain", row.get("returnPathDomain")),
        ("Link features", row.get("linkFeatures")), ("Authentication summary", row.get("authSummary")),
        ("Attachments", "present but stripped" if row.get("hasAttachments") else "none"),
        ("Message body", row.get("sanitizedBody") or row.get("sanitizedText")),
    ]
    return "\n".join(f"{key}: {value}" for key, value in values if value)

def parse_json(text):
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match: return None
    try: return json.loads(match.group(0))
    except json.JSONDecodeError: return None

def load_dataset_split(dataset_dir, split):
    """Read frozen rows ({id, input}) so the baseline uses the EXACT test inputs."""
    path = Path(dataset_dir) / f"{split}.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Reuse the already-built model input verbatim; do not re-derive it.
    return [{"id": row["id"], "_prebuilt_input": row["input"]} for row in rows]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--output-dir", default="baseline_before_training")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--dataset-dir", help="Run the baseline over a frozen split instead of the live DB.")
    parser.add_argument("--split", default="test", help="Frozen split to score when --dataset-dir is given.")
    args = parser.parse_args()
    if args.dataset_dir:
        rows = load_dataset_split(args.dataset_dir, args.split)
    else:
        if not args.database_url: raise SystemExit("Set DATABASE_URL or pass --database-url.")
        rows = load_rows(args.database_url)
    if args.limit: rows = rows[:args.limit]
    if not rows: raise SystemExit("No messages to score. Nothing was run.")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    kwargs = {"torch_dtype": "auto"}
    if args.device == "auto": kwargs["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(MODEL, **kwargs)
    if args.device != "auto": model.to(args.device)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    # Deterministic name when scoring a frozen split so the evaluator can find it.
    output = out / (f"{args.split}-baseline.jsonl" if args.dataset_dir else f"qwen3-0.6b-baseline-{stamp}.jsonl")
    with output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows, 1):
            messages = [{"role":"system", "content":SYSTEM}, {"role":"user", "content":user_content(row)}]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            inputs = tokenizer([text], return_tensors="pt").to(model.device)
            generated = model.generate(**inputs, max_new_tokens=350, do_sample=False, pad_token_id=tokenizer.eos_token_id)
            raw = tokenizer.decode(generated[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()
            record = {"baseline_name":"baseline_before_training", "model":MODEL, "ran_at":datetime.now(timezone.utc).isoformat(), "message_id":row["id"], "input":user_content(row), "raw_output":raw, "prediction":parse_json(raw)}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{index}/{len(rows)}] {row['id']}")
    manifest = {"baseline_name":"baseline_before_training", "model":MODEL, "records":len(rows), "output":str(output), "source_filter":"isSyntheticTestFixture=false; sanitized Wave 1 fields only"}
    (out / f"qwen3-0.6b-baseline-{stamp}.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {output}")
if __name__ == "__main__": main()
