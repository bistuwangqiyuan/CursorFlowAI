import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <article className="prose">
      <h1>Terms of use</h1>
      <p>
        <em>Last updated: 2026-08-03. Informal draft for Gate 0 validation; not legal advice.</em>
      </p>
      <h2>Service</h2>
      <p>
        TriadGuard provides free, automated static analysis of CI workflow configuration you
        voluntarily submit in the browser or run locally via CLI/Action. Continuous monitoring and
        paid subscriptions are not offered until explicitly announced.
      </p>
      <h2>No warranties</h2>
      <p>
        The software is provided “as is” without warranty of any kind. Outputs are heuristic risk
        signals, not security audits, compliance certifications, or professional advice.
      </p>
      <h2>Acceptable use</h2>
      <p>
        Use only on workflows you are authorized to analyze. Do not use the tool to harm systems,
        harass maintainers, or publicly exploit third parties without coordinated disclosure.
      </p>
      <h2>Limitation of liability</h2>
      <p>
        To the maximum extent permitted by law, the operator is not liable for indirect, incidental,
        or consequential damages arising from use of the scanner or reliance on its findings.
      </p>
      <h2>Contact</h2>
      <p>
        Project source and issues:{" "}
        <a href="https://github.com/bistuwangqiyuan/CursorFlowAI">github.com/bistuwangqiyuan/CursorFlowAI</a>
      </p>
    </article>
  );
}
