/**
 * Push local HEAD commit onto origin/main via GitHub Git Data API.
 */
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const REPO = "bistuwangqiyuan/CursorFlowAI";
const ROOT = "d:\\project\\cursor\\bp\\CursorFlowAI";

function ghRaw(args, input) {
  return execFileSync("gh", ["api", ...args], {
    input,
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
}

function gitText(args) {
  return execFileSync("git", ["-C", ROOT, ...args], { encoding: "utf8" }).trim();
}

function gitBuf(args) {
  return execFileSync("git", ["-C", ROOT, ...args], {
    encoding: "buffer",
    maxBuffer: 64 * 1024 * 1024,
  });
}

const head = gitText(["rev-parse", "HEAD"]);
const msg = gitText(["log", "-1", "--format=%B"]);
const nameStatus = gitText(["diff-tree", "--no-commit-id", "--name-status", "-r", head])
  .split(/\r?\n/)
  .filter(Boolean);

console.log("local HEAD", head);
console.log("entries", nameStatus.length);

const treeEntries = [];
for (const row of nameStatus) {
  const tab = row.indexOf("\t");
  const status = row.slice(0, tab);
  const file = row.slice(tab + 1).replace(/\\/g, "/");
  // GitHub Git Data API returns 404 when writing under .github/workflows (workflow ACL).
  if (file.startsWith(".github/workflows/")) {
    console.warn("skip workflow path (API blocked):", file);
    continue;
  }
  if (status.startsWith("D")) {
    throw new Error(`Delete not supported in this pusher: ${file}`);
  }
  const line = gitText(["ls-tree", head, "--", file]);
  const parts = line.split(/\s+/);
  const mode = parts[0];
  const sha = parts[2];
  const content = gitBuf(["cat-file", "-p", sha]);
  const created = JSON.parse(
    ghRaw(
      ["--method", "POST", `repos/${REPO}/git/blobs`, "--input", "-"],
      JSON.stringify({
        content: content.toString("base64"),
        encoding: "base64",
      }),
    ),
  );
  if (!created.sha) {
    throw new Error(`blob create failed for ${file}: ${JSON.stringify(created)}`);
  }
  treeEntries.push({ path: file, mode, type: "blob", sha: created.sha });
  console.log("blob", status, file, created.sha.slice(0, 7));
}

const ref = JSON.parse(ghRaw([`repos/${REPO}/git/ref/heads/main`]));
const baseCommitSha = ref.object.sha;
const baseCommit = JSON.parse(ghRaw([`repos/${REPO}/git/commits/${baseCommitSha}`]));
console.log("base", baseCommitSha, "tree", baseCommit.tree.sha);

const treePayload = {
  base_tree: baseCommit.tree.sha,
  tree: treeEntries,
};
writeFileSync(new URL("./tree-payload.json", import.meta.url), JSON.stringify(treePayload, null, 2));

let treeResp;
try {
  treeResp = ghRaw(
    ["--method", "POST", `repos/${REPO}/git/trees`, "--input", "-"],
    JSON.stringify(treePayload),
  );
} catch (e) {
  // retry without base_tree using only new paths (won't work for full replace)
  console.error("tree create failed, stderr:", e.stderr?.toString?.() || e.message);
  // Try Contents API fallback for a canary file
  throw e;
}

const tree = JSON.parse(treeResp);
console.log("new tree", tree.sha);

const commit = JSON.parse(
  ghRaw(
    ["--method", "POST", `repos/${REPO}/git/commits`, "--input", "-"],
    JSON.stringify({
      message: msg,
      tree: tree.sha,
      parents: [baseCommitSha],
    }),
  ),
);

ghRaw(
  ["--method", "PATCH", `repos/${REPO}/git/refs/heads/main`, "--input", "-"],
  JSON.stringify({ sha: commit.sha, force: false }),
);

console.log("updated main to", commit.sha);
console.log(commit.html_url);
