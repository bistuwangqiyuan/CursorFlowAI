import { writeFileSync } from "node:fs";
import { get } from "node:https";

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    get(url, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    }).on("error", reject);
  });
}

const queries = [
  "GitHub Actions AI agent",
  "prompt injection GitHub Actions",
  "claude code action",
  "AI agent CI/CD security",
  "PromptPwnd",
];

const oneYearAgo = Math.floor(Date.now() / 1000) - 365 * 24 * 3600;
const all = [];

for (const query of queries) {
  const u =
    "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=30&numericFilters=" +
    encodeURIComponent(`created_at_i>${oneYearAgo}`) +
    "&query=" +
    encodeURIComponent(query);
  const j = await fetchJson(u);
  all.push({
    query,
    nbHits: j.nbHits,
    hits: (j.hits || []).map((h) => ({
      title: h.title,
      points: h.points,
      num_comments: h.num_comments,
      created_at: h.created_at,
      url: h.url,
      hn: `https://news.ycombinator.com/item?id=${h.objectID}`,
    })),
  });
}

writeFileSync(new URL("./hn-b2.json", import.meta.url), JSON.stringify(all, null, 2));
const flat = new Map();
for (const block of all) {
  for (const h of block.hits) {
    flat.set(h.hn, h);
  }
}
const unique = [...flat.values()];
const over50 = unique.filter((h) => (h.points || 0) > 50);
console.log(
  JSON.stringify(
    {
      uniqueStories: unique.length,
      over50: over50.length,
      top: unique.sort((a, b) => (b.points || 0) - (a.points || 0)).slice(0, 15),
    },
    null,
    2,
  ),
);
