"""Shared, local-only utilities for Trustfall Qwen training and evaluation."""
import json
import re
from collections import Counter

MODEL = "Qwen/Qwen3-0.6B"
SYSTEM = (
    "You are Trustfall, a scam detection assistant. Analyze only the sanitized "
    "message supplied. Return one JSON object with: risk_level "
    "(safe|low|medium|high|unsure), scam_type, red_flags (array), "
    "recommended_action, plain_english_warning. Do not invent private "
    "information. Be cautious and clear."
)


def placeholder_names(value):
    """Apply the same conservative display cleanup used by the app before ML use."""
    text = value or ""
    text = re.sub(r"(?im)^(hi|dear|hello|hey)\s+[A-Z][a-z]{1,30}\b", r"\1 [PERSON]", text)
    text = re.sub(r"(?im)^(regards|sincerely|thanks|best),?\s*\n\s*[A-Z][a-z]{1,30}\b", r"\1,\n[PERSON]", text)
    return text


def is_reviewable(value):
    text = (value or "").strip()
    compact = re.sub(r"[^\w]", "", text, flags=re.UNICODE).lower()
    if len(compact) < 18 or re.fullmatch(r"(?:as){4,}", compact) or compact == "12wflekfwfijweofijwe":
        return False
    if re.search(r"emailId\?UTF-8\?B\?", text, re.I) or (re.search(r"=\?UTF-8\?", text, re.I) and len(text) > 1800):
        return False
    without_footer = re.sub(r"\[LINK:[^\]]+\]|unsubscribe|manage email preferences", "", text, flags=re.I).strip()
    return not (re.search(r"unsubscribe", text, re.I) and len(without_footer) < 90)


def parse_flags(raw):
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def choose_mode(labels, key):
    counts = Counter(label[key] for label in labels)
    highest = max(counts.values())
    tied = {value for value, count in counts.items() if count == highest}
    return sorted(
        (label for label in labels if label[key] in tied),
        key=lambda label: (-int(label.get("confidence") or 0), str(label.get("createdAt") or "")),
    )[0][key]


def consensus(labels):
    ordered = sorted(labels, key=lambda label: -int(label.get("confidence") or 0))
    flag_counts = Counter(flag for label in labels for flag in parse_flags(label.get("redFlags")))
    flags = [flag for flag, count in flag_counts.items() if count >= 2]
    if not flags:
        flags = [flag for flag, _ in flag_counts.most_common(2)]

    def best(key):
        return next((str(label[key]).strip() for label in ordered if str(label.get(key) or "").strip()), "")

    return {
        "risk_level": choose_mode(labels, "riskLevel"),
        "scam_type": choose_mode(labels, "scamType"),
        "red_flags": flags,
        "recommended_action": best("recommendedAction"),
        "plain_english_warning": best("plainEnglishWarning"),
    }


def agreement(labels, key):
    if not labels:
        return 0.0
    return max(Counter(label[key] for label in labels).values()) / len(labels)


def _stable_hash(identifier):
    number = 0
    for char in identifier:
        number = ((number * 31) + ord(char)) & 0xFFFFFFFF
    return number


def is_train_id(identifier):
    return _stable_hash(identifier) % 10 < 8


def split_bucket(identifier):
    """Deterministic, message-level 70/15/15 train/validation/test assignment.

    The bucket depends only on the message id, so the same message always lands
    in the same split and individual worker labels never leak across splits.
    """
    position = _stable_hash(identifier) % 100
    if position < 70:
        return "train"
    if position < 85:
        return "validation"
    return "test"


def model_input(row):
    entries = [
        ("Subject", row.get("sanitizedSubject")),
        ("From domain", row.get("fromDomain")),
        ("Reply-to domain", row.get("replyToDomain")),
        ("Return-path domain", row.get("returnPathDomain")),
        ("Link features", row.get("linkFeatures")),
        ("Authentication summary", row.get("authSummary")),
        ("Attachments", "present but stripped" if row.get("hasAttachments") else "none"),
        ("Message body", row.get("sanitizedBody") or row.get("sanitizedText")),
    ]
    return "\n".join(f"{key}: {placeholder_names(str(value))}" for key, value in entries if value)


def parse_model_json(text):
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None
