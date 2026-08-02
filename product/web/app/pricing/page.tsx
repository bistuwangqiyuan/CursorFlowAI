import type { Metadata } from "next";

export const metadata: Metadata = { title: "Pricing" };

export default function PricingPage() {
  return (
    <article className="prose">
      <h1>Pricing</h1>
      <p>
        <span className="badge">Checkout closed · Gate 0 / Gate 1</span>
      </p>
      <p>
        Planned self-serve prices (from the business plan unit economics).{" "}
        <strong>Continuous monitoring is not available yet.</strong> Today you get free one-shot
        scanning only.
      </p>

      <table>
        <thead>
          <tr>
            <th>Tier</th>
            <th>Price</th>
            <th>What it is</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Free scan</td>
            <td>$0</td>
            <td>Browser / CLI / GitHub Action one-shot scan. Full findings, always.</td>
            <td>Available</td>
          </tr>
          <tr>
            <td>Monitor</td>
            <td>$19 / mo</td>
            <td>
              Planned: hosted continuous monitoring, drift alerts, historical baseline. Not a
              “compliance certificate.”
            </td>
            <td>Not open</td>
          </tr>
          <tr>
            <td>Team</td>
            <td>$49 / mo</td>
            <td>Planned: multi-repo monitoring for small teams.</td>
            <td>Not open</td>
          </tr>
          <tr>
            <td>Founding prepay</td>
            <td>$99 one-time</td>
            <td>
              Gate 1 willingness-to-pay test (covers year-1 monitor intent). Opens only after Gate
              0-B passes. Refund policy will be stated before any charge.
            </td>
            <td>Not open</td>
          </tr>
        </tbody>
      </table>

      <h2>What you are not buying</h2>
      <ul>
        <li>No human customer support at these prices (stated up front).</li>
        <li>No auto-merge fix PRs.</li>
        <li>No general SAST/SCA.</li>
        <li>No “you are compliant” verdicts.</li>
      </ul>

      <p>
        Payments, if ever opened, will use Paddle as Merchant of Record. Stripe direct is not
        available for mainland China sole proprietors (see Gate 0 docs).
      </p>
    </article>
  );
}
