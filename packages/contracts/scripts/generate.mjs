// Generate src/generated/openapi.ts from openapi.json with openapi-typescript (P0-13, ADR 0020).
//   node scripts/generate.mjs           write the file
//   node scripts/generate.mjs --check   exit 1 if the committed file is stale (runs in `pnpm test`)
// openapi.json itself comes from the API: uv run python apps/api/scripts/export_openapi.py
// (.\tasks.ps1 contracts runs both steps).
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const input = join(root, "openapi.json");
const output = join(root, "src", "generated", "openapi.ts");
const HEADER = [
  "/**",
  " * Generated from packages/contracts/openapi.json by scripts/generate.mjs. Do not edit by hand.",
  " * Regenerate after changing the API: .\\tasks.ps1 contracts",
  " */",
  "",
  "",
].join("\n");

const schema = JSON.parse(readFileSync(input, "utf8"));
const text = (HEADER + astToString(await openapiTS(schema))).replace(/\r\n/g, "\n");
const current = existsSync(output) ? readFileSync(output, "utf8").replace(/\r\n/g, "\n") : null;

if (process.argv.includes("--check")) {
  if (current !== text) {
    console.error(`${output} is out of date. Run: .\\tasks.ps1 contracts`);
    process.exit(1);
  }
  console.log("generated client is up to date");
} else if (current === text) {
  console.log(`unchanged: ${output}`);
} else {
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, text);
  console.log(`wrote ${output}`);
}
