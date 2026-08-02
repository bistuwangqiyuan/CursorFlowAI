import { parseDocument } from "yaml";
import {
  AGENT_ACTIONS,
  EXFIL_SHELL_PATTERNS,
  HIGH_PRIVILEGE_KEYS,
  UNTRUSTED_EVENTS,
} from "./agents.js";
import { findLine, normalizeTriggers } from "./line.js";
import { SOURCES } from "./sources.js";
import type { Finding, ScanOptions, ScanResult, TriangleLeg } from "./types.js";

const DISCLAIMER =
  "TriadGuard reports configuration risk signals only. It does not certify compliance, security, or fitness for any purpose.";

function collectRunScripts(node: unknown, out: string[]): void {
  if (node == null) return;
  if (typeof node === "string") {
    out.push(node);
    return;
  }
  if (Array.isArray(node)) {
    for (const item of node) collectRunScripts(item, out);
    return;
  }
  if (typeof node === "object") {
    const obj = node as Record<string, unknown>;
    if (typeof obj.run === "string") out.push(obj.run);
    if (typeof obj.run === "object") collectRunScripts(obj.run, out);
    for (const value of Object.values(obj)) {
      if (value !== obj.run) collectRunScripts(value, out);
    }
  }
}

function permissionsText(perms: unknown): string {
  if (perms == null) return "";
  if (typeof perms === "string") return perms;
  try {
    return JSON.stringify(perms);
  } catch {
    return String(perms);
  }
}

function detectAgents(source: string): { label: string; line?: number }[] {
  const hits: { label: string; line?: number }[] = [];
  for (const agent of AGENT_ACTIONS) {
    if (agent.pattern.test(source)) {
      hits.push({ label: agent.label, line: findLine(source, agent.pattern) });
    }
  }
  return hits;
}

function detectUntrusted(triggers: string[], source: string): { event: string; line?: number }[] {
  const hits: { event: string; line?: number }[] = [];
  for (const event of UNTRUSTED_EVENTS) {
    if (triggers.includes(event) || new RegExp(`\\b${event}\\b`).test(source)) {
      hits.push({ event, line: findLine(source, new RegExp(`\\b${event}\\b`)) });
    }
  }
  return hits;
}

function detectHighPrivilege(source: string, doc: unknown): { detail: string; line?: number }[] {
  const hits: { detail: string; line?: number }[] = [];
  const root = (doc && typeof doc === "object" ? doc : {}) as Record<string, unknown>;
  const blobs: string[] = [permissionsText(root.permissions)];

  const jobs = root.jobs;
  if (jobs && typeof jobs === "object") {
    for (const job of Object.values(jobs as Record<string, unknown>)) {
      if (job && typeof job === "object") {
        blobs.push(permissionsText((job as Record<string, unknown>).permissions));
      }
    }
  }

  const joined = `${source}\n${blobs.join("\n")}`;
  for (const key of HIGH_PRIVILEGE_KEYS) {
    const re =
      key === "write-all"
        ? /permissions:\s*write-all\b|['"]write-all['"]/i
        : new RegExp(key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i");
    if (re.test(joined) || re.test(source)) {
      hits.push({ detail: key, line: findLine(source, re) });
    }
  }
  return hits;
}

function detectExfil(source: string, doc: unknown): { detail: string; line?: number }[] {
  const hits: { detail: string; line?: number }[] = [];
  const scripts: string[] = [];
  collectRunScripts(doc, scripts);

  // Agent actions that can execute arbitrary model-suggested commands are an exfil path
  // when combined with untrusted input (PromptPwnd class). Flag explicit network/shell tools.
  for (const script of scripts) {
    for (const p of EXFIL_SHELL_PATTERNS) {
      if (p.pattern.test(script)) {
        hits.push({
          detail: p.label,
          line: findLine(source, p.pattern),
        });
      }
    }
  }

  // Broad network / command-capable agent inputs commonly documented in PromptPwnd
  const agentExfilFlags = [
    /prompt_injection|allow_network|network:\s*true|bash_tool|enable_bash/i,
    /claude_args:.*--dangerously-skip-permissions/i,
    /permission_mode:\s*['"]?bypass/i,
  ];
  for (const re of agentExfilFlags) {
    if (re.test(source)) {
      hits.push({ detail: "agent-exec/network flag", line: findLine(source, re) });
    }
  }

  // If an agent action is present, the model can typically run tools → latent exfil path.
  // Represented as info-level leg; critical only when combined (see combine).
  if (detectAgents(source).length > 0) {
    const already = hits.some((h) => h.detail === "agent-tool-execution");
    if (!already) {
      hits.push({
        detail: "agent-tool-execution",
        line: detectAgents(source)[0]?.line,
      });
    }
  }

  return hits;
}

function uniqByDetail<T extends { detail?: string; event?: string; label?: string }>(
  items: T[],
  key: (t: T) => string,
): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const item of items) {
    const k = key(item);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(item);
  }
  return out;
}

export function scanWorkflow(source: string, options: ScanOptions = {}): ScanResult {
  const filename = options.filename ?? "workflow.yml";
  const findings: Finding[] = [];
  let doc: unknown = null;

  try {
    doc = parseDocument(source).toJSON();
  } catch (err) {
    findings.push({
      ruleId: "TG-PARSE",
      severity: "warn",
      title: "YAML parse error",
      message: err instanceof Error ? err.message : String(err),
      legs: [],
      file: filename,
      remediation: "Fix YAML syntax, then re-scan.",
      sources: [],
    });
    return finalize(filename, findings);
  }

  const triggers = normalizeTriggers(
    doc && typeof doc === "object" ? (doc as Record<string, unknown>).on : undefined,
  );

  const agents = uniqByDetail(detectAgents(source), (a) => a.label);
  const untrusted = uniqByDetail(detectUntrusted(triggers, source), (u) => u.event);
  const privileges = uniqByDetail(detectHighPrivilege(source, doc), (p) => p.detail);
  // Exclude latent agent-tool-execution from "explicit" shell exfil for messaging clarity
  const exfilAll = uniqByDetail(detectExfil(source, doc), (e) => e.detail);
  const explicitExfil = exfilAll.filter((e) => e.detail !== "agent-tool-execution");
  const latentAgentExfil = exfilAll.filter((e) => e.detail === "agent-tool-execution");

  for (const a of agents) {
    findings.push({
      ruleId: "TG-AGENT",
      severity: "info",
      title: "AI agent action detected",
      message: `Workflow uses agent action \`${a.label}\`.`,
      legs: ["agent"],
      file: filename,
      line: a.line,
      remediation:
        "Pin the action to a full commit SHA; restrict which events can invoke it; never feed untrusted PR/issue text into the agent prompt without sanitization.",
      sources: [SOURCES.AIKIDO_PROMPTPWND, SOURCES.CSA_AI_GHA],
    });
  }

  for (const u of untrusted) {
    findings.push({
      ruleId: "TG-UNTRUSTED",
      severity: u.event === "pull_request_target" ? "warn" : "info",
      title: "Untrusted trigger event",
      message: `Workflow may run on \`${u.event}\`, which can carry attacker-controlled content.`,
      legs: ["untrusted_input"],
      file: filename,
      line: u.line,
      remediation:
        "Prefer `pull_request` (fork PR from untrusted code context) over `pull_request_target` for untrusted contributors; do not pass issue/PR body into privileged agent prompts.",
      sources: [SOURCES.GITHUB_PR_TARGET, SOURCES.CSA_AI_GHA],
    });
  }

  for (const p of privileges) {
    findings.push({
      ruleId: "TG-PRIV",
      severity: "warn",
      title: "High privilege credentials",
      message: `Elevated permission detected: \`${p.detail}\`.`,
      legs: ["high_privilege"],
      file: filename,
      line: p.line,
      remediation:
        "Apply least privilege: drop `write-all`; scope `contents`/`pull-requests` to `read` unless a specific step needs write; isolate agent jobs from deploy secrets.",
      sources: [SOURCES.NOMA_GITLOST, SOURCES.AIKIDO_PROMPTPWND],
    });
  }

  for (const e of explicitExfil) {
    findings.push({
      ruleId: "TG-EXFIL",
      severity: "warn",
      title: "Potential exfiltration / write path",
      message: `Command or flag associated with data egress or mutation: \`${e.detail}\`.`,
      legs: ["exfiltration"],
      file: filename,
      line: e.line,
      remediation:
        "Remove network/write tools from agent-reachable steps; block outbound egress; require human approval for mutating commands.",
      sources: [SOURCES.AIKIDO_PROMPTPWND, SOURCES.NOMA_GITLOST],
    });
  }

  const hasAgent = agents.length > 0;
  const hasUntrusted = untrusted.length > 0;
  const hasPriv = privileges.length > 0;
  const hasExfil = explicitExfil.length > 0 || latentAgentExfil.length > 0;

  // Fatal triangle per BP: untrusted input × high privilege × exfil path, in presence of agent
  if (hasAgent && hasUntrusted && hasPriv && hasExfil) {
    const line =
      agents[0]?.line ?? untrusted[0]?.line ?? privileges[0]?.line ?? explicitExfil[0]?.line;
    findings.push({
      ruleId: "TG-TRIAD",
      severity: "critical",
      title: "Fatal triangle: agent + untrusted input + privilege + exfil path",
      message:
        "This workflow combines an AI agent action, an untrusted trigger, elevated permissions, and an execution/egress path. An attacker who controls issue/PR content may coerce the agent to abuse credentials.",
      legs: ["agent", "untrusted_input", "high_privilege", "exfiltration"],
      file: filename,
      line,
      remediation: [
        "1) Remove `pull_request_target` / untrusted comment triggers for agent jobs, or require maintainer labeling before agent runs.",
        "2) Drop write permissions and secrets from the agent job.",
        "3) Disable network / bash tools for the agent; never pass raw issue/PR bodies into prompts.",
        "4) Keep findings public to maintainers — do not hide fixes behind a paywall.",
      ].join(" "),
      sources: [SOURCES.AIKIDO_PROMPTPWND, SOURCES.NOMA_GITLOST, SOURCES.CSA_AI_GHA],
    });
  } else if (hasAgent && hasUntrusted && (hasPriv || hasExfil)) {
    findings.push({
      ruleId: "TG-NEAR-TRIAD",
      severity: "critical",
      title: "Near-fatal combination",
      message:
        "AI agent runs on untrusted input with elevated privilege and/or an egress path. Treat as high risk even if one leg is only latent.",
      legs: [
        "agent",
        "untrusted_input",
        ...(hasPriv ? (["high_privilege"] as TriangleLeg[]) : []),
        ...(hasExfil ? (["exfiltration"] as TriangleLeg[]) : []),
      ],
      file: filename,
      line: agents[0]?.line ?? untrusted[0]?.line,
      remediation:
        "Break at least one leg: trusted triggers only, read-only permissions, and no tool/network access for the agent.",
      sources: [SOURCES.AIKIDO_PROMPTPWND, SOURCES.CSA_AI_GHA],
    });
  }

  return finalize(filename, findings);
}

function finalize(filename: string, findings: Finding[]): ScanResult {
  const legsPresent = Array.from(
    new Set(findings.flatMap((f) => f.legs)),
  ) as TriangleLeg[];
  return {
    filename,
    findings,
    summary: {
      critical: findings.filter((f) => f.severity === "critical").length,
      warn: findings.filter((f) => f.severity === "warn").length,
      info: findings.filter((f) => f.severity === "info").length,
      legsPresent,
      fatalTriangle: findings.some((f) => f.ruleId === "TG-TRIAD" || f.ruleId === "TG-NEAR-TRIAD"),
    },
    disclaimer: DISCLAIMER,
  };
}
