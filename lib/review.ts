/** Reject only records that cannot be meaningfully labeled; all other real worker data stays eligible. */
export function isReviewableForLabeling(value: string) {
  const text = value.trim();
  const compact = text.replace(/[^\p{L}\p{N}]/gu, "").toLowerCase();
  if (compact.length < 18) return false;
  if (/^(?:as){4,}$|^12wflekfwfijweofijwe$/i.test(compact)) return false;
  if (/emailId\?UTF-8\?B\?/i.test(text) || (/=\?UTF-8\?/i.test(text) && text.length > 1800)) return false;
  const withoutLinks = text.replace(/\[LINK:[^\]]+\]/g, "").replace(/unsubscribe|manage email preferences/gi, "").trim();
  if (/unsubscribe/i.test(text) && withoutLinks.length < 90) return false;
  return true;
}
