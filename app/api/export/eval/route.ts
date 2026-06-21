import { evalJson } from "@/lib/exportData";
export async function GET() { return Response.json(await evalJson(), { headers: { "Content-Disposition": "attachment; filename=trustfall-eval.json" } }); }
