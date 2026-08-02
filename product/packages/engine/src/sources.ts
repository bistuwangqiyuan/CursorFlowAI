import type { SourceRef } from "./types.js";

/** Evidence anchors — cross-check research/sources.md (CursorFlowAI BP). */
export const SOURCES = {
  AIKIDO_PROMPTPWND: {
    id: "aikido-promptpwnd",
    title: "Aikido PromptPwnd — AI agents in CI/CD prompt injection",
    url: "https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents",
  },
  NOMA_GITLOST: {
    id: "noma-gitlost",
    title: "Noma Security GitLost — GitHub AI agent private repo leak",
    url: "https://noma.security/blog/gitlost-how-we-tricked-githubs-ai-agent-into-leaking-private-repos/",
  },
  CSA_AI_GHA: {
    id: "csa-ai-gha-20260503",
    title: "CSA research note — AI GitHub Actions security (2026-05-03)",
    url: "https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/05/CSA_research_note_ai_github_actions_security_20260503-csa-styled.pdf",
  },
  GITHUB_PR_TARGET: {
    id: "github-pull-request-target",
    title: "GitHub Docs — Events that trigger workflows (pull_request_target)",
    url: "https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request_target",
  },
} as const satisfies Record<string, SourceRef>;
