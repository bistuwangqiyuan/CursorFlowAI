import { writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const queries = [
  "path:.github/workflows anthropics/claude-code-action",
  "path:.github/workflows google-github-actions/run-gemini-cli",
  "path:.github/workflows openai/codex-action",
  "path:.github/workflows pull_request_target claude-code-action",
  "path:.github/workflows permissions: write-all claude-code-action",
];

const results = [];
for (const q of queries) {
  try {
    const out = execFileSync(
      "gh",
      ["api", `search/code?per_page=1&q=${encodeURIComponent(q)}`, "--jq", "{total_count,incomplete_results}"],
      { encoding: "utf8" },
    );
    results.push({ query: q, ...JSON.parse(out) });
  } catch (e) {
    results.push({
      query: q,
      error: e.stderr?.toString?.() || String(e),
    });
  }
}

writeFileSync(new URL("./github-b1.json", import.meta.url), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
