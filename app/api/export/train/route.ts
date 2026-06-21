import { trainJsonl } from "@/lib/exportData";
export async function GET() { return new Response(await trainJsonl(), { headers: { "Content-Type": "application/jsonl; charset=utf-8", "Content-Disposition": "attachment; filename=trustfall-train.jsonl" } }); }
