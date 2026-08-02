import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <article className="prose">
      <h1>Privacy</h1>
      <p>
        <em>Last updated: 2026-08-03.</em>
      </p>
      <h2>Browser scan</h2>
      <p>
        Workflow YAML pasted or uploaded in the browser is processed <strong>locally in your
        browser</strong>. We do not receive or store the file contents on our servers.
      </p>
      <h2>Analytics</h2>
      <p>
        We use Vercel Analytics for aggregate traffic (unique visitors) and may record an anonymous{" "}
        <code>scan_completed</code> event with counts of finding severities — never the YAML itself.
        This exists to measure Gate 0-B (300 UV / 30 uses in 14 days).
      </p>
      <h2>CLI / Action</h2>
      <p>
        Local CLI and GitHub Action scans run on your machine or runner. Telemetry is{" "}
        <strong>off by default</strong>.
      </p>
      <h2>No accounts (Gate 0)</h2>
      <p>We do not offer accounts, OAuth, or customer databases in Gate 0.</p>
      <h2>Payments</h2>
      <p>
        No payment processing is enabled. If opened later, Paddle (Merchant of Record) will process
        payments under their privacy terms.
      </p>
    </article>
  );
}
