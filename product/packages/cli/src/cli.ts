#!/usr/bin/env node
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { scanWorkflow, type ScanResult } from "@triadguard/engine";

function printHelp(): void {
  console.log(`TriadGuard — AI agent CI/CD fatal-triangle scanner (zero LLM)

Usage:
  triadguard [paths...]
  triadguard --json [paths...]
  npx triadguard .github/workflows

Defaults to .github/workflows when no paths given.

Exit codes:
  0  no critical findings
  1  critical findings present
  2  usage / IO error

Privacy: scans run locally. No workflow contents are uploaded.
Optional anonymous usage ping is OFF by default (TRIADGUARD_TELEMETRY=1 to enable later).
`);
}

function collectYamlFiles(path: string): string[] {
  const st = statSync(path);
  if (st.isFile()) {
    return /\.ya?ml$/i.test(path) ? [path] : [];
  }
  const out: string[] = [];
  for (const name of readdirSync(path)) {
    const full = join(path, name);
    const s = statSync(full);
    if (s.isDirectory()) out.push(...collectYamlFiles(full));
    else if (/\.ya?ml$/i.test(name)) out.push(full);
  }
  return out;
}

function formatText(results: ScanResult[]): string {
  const lines: string[] = [];
  for (const r of results) {
    lines.push(`\n=== ${r.filename} ===`);
    if (r.findings.length === 0) {
      lines.push("No findings.");
      continue;
    }
    for (const f of r.findings) {
      const loc = f.line ? `:${f.line}` : "";
      lines.push(`[${f.severity.toUpperCase()}] ${f.ruleId} ${r.filename}${loc}`);
      lines.push(`  ${f.title}`);
      lines.push(`  ${f.message}`);
      lines.push(`  Fix: ${f.remediation}`);
    }
    lines.push(
      `Summary: critical=${r.summary.critical} warn=${r.summary.warn} info=${r.summary.info} fatalTriangle=${r.summary.fatalTriangle}`,
    );
    lines.push(r.disclaimer);
  }
  return lines.join("\n");
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  if (argv.includes("-h") || argv.includes("--help")) {
    printHelp();
    process.exit(0);
  }
  const json = argv.includes("--json");
  const paths = argv.filter((a) => !a.startsWith("-"));
  const targets = paths.length > 0 ? paths : [".github/workflows"];

  const files: string[] = [];
  for (const t of targets) {
    try {
      files.push(...collectYamlFiles(t));
    } catch (err) {
      console.error(`Cannot read ${t}:`, err instanceof Error ? err.message : err);
      process.exit(2);
    }
  }

  if (files.length === 0) {
    console.error("No YAML workflow files found.");
    process.exit(2);
  }

  const results: ScanResult[] = files.map((file) => {
    const source = readFileSync(file, "utf8");
    return scanWorkflow(source, { filename: relative(process.cwd(), file) || file });
  });

  if (json) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    console.log(formatText(results));
  }

  const critical = results.some((r) => r.summary.critical > 0);
  process.exit(critical ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
