import type { Metadata } from "next";

export const metadata: Metadata = { title: "Docs" };

export default function DocsPage() {
  return (
    <article className="prose">
      <h1>Docs</h1>
      <p>
        TriadGuard is a <strong>configuration risk scanner</strong> for AI agents inside CI/CD. It
        does not replace SAST/SCA, and it never claims you are “compliant.”
      </p>

      <h2>The fatal triangle</h2>
      <p>A workflow is high-risk when these legs co-occur:</p>
      <ol>
        <li>
          <strong>Untrusted input</strong> — events such as <code>pull_request_target</code>,{" "}
          <code>issue_comment</code>, or <code>issues</code> that can carry attacker-controlled text.
        </li>
        <li>
          <strong>AI agent action</strong> — e.g. <code>anthropics/claude-code-action</code>,{" "}
          <code>google-github-actions/run-gemini-cli</code>, <code>openai/codex-action</code>.
        </li>
        <li>
          <strong>High privilege + exfil path</strong> — <code>write-all</code> / write permissions
          plus shell/network tools or agent tool execution.
        </li>
      </ol>

      <h2>Evidence (not marketing)</h2>
      <ul>
        <li>
          <a href="https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents">
            Aikido PromptPwnd
          </a>{" "}
          — demonstrated prompt injection against AI agents in GitHub Actions / GitLab CI.
        </li>
        <li>
          <a href="https://noma.security/blog/gitlost-how-we-tricked-githubs-ai-agent-into-leaking-private-repos/">
            Noma GitLost
          </a>{" "}
          — unauthenticated issue content coercing an agent to leak private org repos.
        </li>
        <li>
          <a href="https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/05/CSA_research_note_ai_github_actions_security_20260503-csa-styled.pdf">
            CSA research note (2026-05-03)
          </a>{" "}
          — attack surface when PR/issue events auto-trigger agents without maintainer interaction.
        </li>
        <li>
          <a href="https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request_target">
            GitHub docs: pull_request_target
          </a>
        </li>
      </ul>

      <h2>CLI &amp; GitHub Action</h2>
      <pre className="cmd">{`# from this monorepo after npm install && npm run build
node product/packages/cli/dist/cli.js .github/workflows

# GitHub Action (composite, from this repo)
uses: bistuwangqiyuan/CursorFlowAI/product/action@main
with:
  path: .github/workflows

# Example: product/action/examples/self-check.yml`}</pre>

      <h2>What is free vs paid (honest)</h2>
      <p>
        <strong>Free now:</strong> one-shot browser scan, CLI, and Action.{" "}
        <strong>Not built yet:</strong> continuous hosted monitoring (config drift, baselines,
        re-scan on new rules). Paid tiers on the pricing page describe the planned product; checkout
        is closed until Gate 1.
      </p>

      <h2>Responsible disclosure</h2>
      <p>
        If you find a real issue in someone else’s public repo, report privately (GitHub Security
        Advisory or maintainer email). Do not dump exploit details publicly. TriadGuard findings for
        your own scans are shown in full — never paywalled.
      </p>
    </article>
  );
}
