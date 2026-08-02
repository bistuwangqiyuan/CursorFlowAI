"use client";

import { scanWorkflow, type Finding, type ScanResult } from "@triadguard/engine";
import { useState, useTransition } from "react";

const SAMPLE = `name: agent-review
on:
  pull_request_target:
    types: [opened, synchronize]
permissions: write-all
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            Review this PR. Body: \${{ github.event.pull_request.body }}
      - run: curl -X POST https://example.com/hook -d "ok"
`;

function trackScanCompleted(summary: ScanResult["summary"]): void {
  try {
    const key = "tg_scan_count";
    const prev = Number(localStorage.getItem(key) || "0");
    localStorage.setItem(key, String(prev + 1));
  } catch {
    /* ignore */
  }
  // Vercel Analytics custom event (no file contents)
  try {
    const w = window as Window & {
      va?: (event: string, data?: Record<string, unknown>) => void;
    };
    w.va?.("scan_completed", {
      critical: summary.critical,
      fatalTriangle: summary.fatalTriangle,
    });
  } catch {
    /* ignore */
  }
}

function FindingCard({ f, file }: { f: Finding; file: string }) {
  return (
    <article className={`finding ${f.severity}`}>
      <div className="meta">
        {f.severity.toUpperCase()} · {f.ruleId}
        {f.line ? ` · ${file}:${f.line}` : ""}
      </div>
      <h3>{f.title}</h3>
      <p>{f.message}</p>
      <p>
        <strong>Fix:</strong> {f.remediation}
      </p>
      {f.sources.length > 0 && (
        <p className="hint">
          Sources:{" "}
          {f.sources.map((s, i) => (
            <span key={s.id}>
              {i > 0 ? " · " : ""}
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.title}
              </a>
            </span>
          ))}
        </p>
      )}
    </article>
  );
}

export function Scanner() {
  const [yaml, setYaml] = useState(SAMPLE);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [pending, startTransition] = useTransition();

  function runScan(source: string) {
    startTransition(() => {
      const r = scanWorkflow(source, { filename: "workflow.yml" });
      setResult(r);
      trackScanCompleted(r.summary);
    });
  }

  return (
    <section className="panel" aria-label="Workflow scanner">
      <label htmlFor="workflow">Paste a GitHub Actions workflow YAML</label>
      <textarea
        id="workflow"
        value={yaml}
        onChange={(e) => setYaml(e.target.value)}
        spellCheck={false}
        aria-describedby="scan-privacy"
      />
      <div className="toolbar">
        <button type="button" className="btn btn-primary" disabled={pending} onClick={() => runScan(yaml)}>
          {pending ? "Scanning…" : "Scan in browser"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setYaml(SAMPLE)}>
          Load sample
        </button>
        <label className="btn btn-ghost" style={{ cursor: "pointer" }}>
          Upload file
          <input
            type="file"
            accept=".yml,.yaml,text/yaml"
            hidden
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const text = await file.text();
              setYaml(text);
              runScan(text);
            }}
          />
        </label>
      </div>
      <p id="scan-privacy" className="hint">
        Privacy: parsing runs entirely in your browser. Workflow contents are not uploaded to our
        servers. We only record an anonymous <code>scan_completed</code> event for Gate 0 traffic
        measurement.
      </p>

      {result && (
        <div className="findings">
          <p>
            <span className="badge">
              critical {result.summary.critical} · warn {result.summary.warn} · info{" "}
              {result.summary.info}
            </span>
            {result.summary.fatalTriangle ? " · fatal / near-fatal triangle detected" : ""}
          </p>
          {result.findings.map((f, i) => (
            <FindingCard key={`${f.ruleId}-${i}`} f={f} file={result.filename} />
          ))}
          <p className="hint">{result.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
