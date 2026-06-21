export type LabelLike = { riskLevel: string; scamType: string; redFlags: string; recommendedAction: string; plainEnglishWarning: string; confidence: number; createdAt?: Date };
const mode = (labels: LabelLike[], key: "riskLevel" | "scamType") => {
  const counts = new Map<string, number>(); labels.forEach(label => counts.set(label[key], (counts.get(label[key]) ?? 0) + 1));
  const max = Math.max(...counts.values()); const tied = [...counts.entries()].filter(([, count]) => count === max).map(([value]) => value);
  return labels.filter(label => tied.includes(label[key])).sort((a, b) => b.confidence - a.confidence || (a.createdAt?.getTime() ?? 0) - (b.createdAt?.getTime() ?? 0))[0]?.[key] ?? "unsure";
};
export function consensus(labels: LabelLike[]) {
  const sorted = [...labels].sort((a,b) => b.confidence - a.confidence);
  const flags = new Map<string, number>();
  labels.forEach(l => { try { JSON.parse(l.redFlags).forEach((f: string) => flags.set(f, (flags.get(f) ?? 0) + 1)); } catch {} });
  let redFlags = [...flags.entries()].filter(([, count]) => count >= 2).map(([flag]) => flag);
  if (!redFlags.length) redFlags = [...flags.entries()].sort((a,b) => b[1] - a[1]).slice(0, 2).map(([flag]) => flag);
  const best = (key: "recommendedAction" | "plainEnglishWarning") => sorted.find(l => l[key].trim())?.[key].trim() ?? "";
  return { risk_level: mode(labels, "riskLevel"), scam_type: mode(labels, "scamType"), red_flags: redFlags, recommended_action: best("recommendedAction"), plain_english_warning: best("plainEnglishWarning") };
}
export function isTrainId(id: string) { let n = 0; for (const c of id) n = (n * 31 + c.charCodeAt(0)) >>> 0; return n % 10 < 8; }
