export function teracCallbackUrl(id: string) {
  const base = process.env.TERAC_CALLBACK_BASE_URL;
  if (!base) return `/terac/complete?callback=local&teracSubmissionId=${encodeURIComponent(id)}`;
  const url = new URL(base);
  url.searchParams.set("teracSubmissionId", id);
  url.searchParams.set("result", "completed");
  return url.toString();
}
