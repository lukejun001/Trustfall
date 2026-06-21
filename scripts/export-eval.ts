import { evalJson } from "../lib/exportData";
process.stdout.write(JSON.stringify(await evalJson(), null, 2) + "\n");
