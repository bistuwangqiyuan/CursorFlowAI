/** Known AI-agent GitHub Actions (BP C12 named set + documented aliases). */
export const AGENT_ACTIONS: readonly {
  pattern: RegExp;
  label: string;
}[] = [
  {
    pattern: /anthropics\/claude-code-action(@|$|\/)/i,
    label: "anthropics/claude-code-action",
  },
  {
    pattern: /google-github-actions\/run-gemini-cli(@|$|\/)/i,
    label: "google-github-actions/run-gemini-cli",
  },
  {
    pattern: /openai\/codex-action(@|$|\/)/i,
    label: "openai/codex-action",
  },
  {
    // Documented alias family used in PromptPwnd writeups
    pattern: /github\/ai-inference(@|$|\/)/i,
    label: "github/ai-inference",
  },
];

export const UNTRUSTED_EVENTS = [
  "pull_request_target",
  "issue_comment",
  "issues",
  "pull_request_review_comment",
  "discussion_comment",
] as const;

export const HIGH_PRIVILEGE_KEYS = [
  "write-all",
  "contents: write",
  "contents:write",
  "id-token: write",
  "id-token:write",
  "packages: write",
  "packages:write",
  "pull-requests: write",
  "pull-requests:write",
  "actions: write",
  "actions:write",
] as const;

export const EXFIL_SHELL_PATTERNS: readonly {
  pattern: RegExp;
  label: string;
}[] = [
  { pattern: /\bcurl\b/i, label: "curl" },
  { pattern: /\bwget\b/i, label: "wget" },
  { pattern: /\bnc\b|\bncat\b/i, label: "netcat" },
  { pattern: /\bgh\s+(api|repo|secret|gist)\b/i, label: "gh write/api" },
  { pattern: /\bgit\s+push\b/i, label: "git push" },
  { pattern: /\baws\s+/i, label: "aws cli" },
  { pattern: /\bkubectl\b/i, label: "kubectl" },
];
