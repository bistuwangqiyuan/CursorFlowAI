/**
 * B1 support: GitHub code search via API (unauthenticated rate limits apply).
 * Keyword volume / KD from Ahrefs|Semrush still require a human free-tier check —
 * recorded separately in EVIDENCE.md.
 */
import { writeFileSync } from "node:fs";
import { get } from "node:https";

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    get(
      url,
      {
        headers: {
          "User-Agent": "TriadGuard-Gate0/0.1",
          Accept: "application/vnd.github+json",
        },
      },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(data) });
          } catch (e) {
            resolve({ status: res.statusCode, body: data });
          }
        });
      },
    ).on("error", reject);
  });
}

const queries = [
  "path:.github/workflows anthropics/claude-code-action",
  "path:.github/workflows google-github-actions/run-gemini-cli",
  "path:.github/workflows openai/codex-action",
  "path:.github/workflows pull_request_target claude-code-action",
];

const results = [];
for (const q of queries) {
  const url =
    "https://api.github.com/search/code?per_page=1&q=" + encodeURIComponent(q);
  const r = await fetchJson(url);
  results.push({
    query: q,
    status: r.status,
    total_count: r.body?.total_count ?? null,
    incomplete_results: r.body?.incomplete_results ?? null,
    note:
      r.status === 401 || r.status === 403
        ? "GitHub code search often requires auth; treat null as unverified."
        : "ok",
  });
  await new Promise((r) => setTimeout(r, 1500));
}

writeFileSync(new URL("./github-b1.json", import.meta.url), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
