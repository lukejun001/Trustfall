export const SOURCES = ["sms", "email", "dm", "marketplace", "job_post", "payment_app", "other"] as const;
export const BELIEFS = ["suspicious", "legitimate", "unsure"] as const;
export const RISKS = ["safe", "low", "medium", "high", "unsure"] as const;
export const SCAM_TYPES = ["not_scam", "delivery_phishing", "bank_phishing", "fake_job", "fake_check", "crypto", "romance", "marketplace", "tech_support", "government_impersonation", "account_takeover", "payment_app", "other", "unsure"] as const;
export const RED_FLAGS = ["urgent_language", "suspicious_link", "asks_for_payment", "asks_for_password_or_code", "too_good_to_be_true", "impersonates_trusted_brand", "weird_sender_or_domain", "threatens_consequences", "asks_to_move_off_platform", "requests_personal_info", "unusual_payment_method", "poor_grammar_or_formatting", "none"] as const;
export const humanize = (value: string) => value.replaceAll("_", " ");
