import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Gate 0" };

export default function Gate0Page() {
  return (
    <article className="prose">
      <h1>Gate 0 — public kill criteria</h1>
      <p>
        This project follows a written business plan:{" "}
        <strong>no hosted SaaS until traffic and payment rails are proven</strong>. Standards are
        public so we cannot quietly move the goalposts.
      </p>

      <h2>Pass / fail (objective)</h2>
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Pass criteria</th>
            <th>On fail</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>0-A Paddle</td>
            <td>Seller KYC approved; payout method accepted; site/legal pages available</td>
            <td>Entity fallbacks, then stop commercialization if all fail</td>
          </tr>
          <tr>
            <td>0-B B3 traffic</td>
            <td>
              Within <strong>14 days</strong> of launch: ≥ <strong>300</strong> real unique visitors
              and ≥ <strong>30</strong> actual uses (browser scan / CLI / Action)
            </td>
            <td>Abandon C12 candidate (or retry next candidate, max 2 retries)</td>
          </tr>
          <tr>
            <td>Gate 1 (later)</td>
            <td>≥ 3 real $99 prepays after prices are shown</td>
            <td>No product-dev hours for monitoring MVP</td>
          </tr>
        </tbody>
      </table>

      <h2>What is shipping in Gate 0</h2>
      <ul>
        <li>This site + in-browser scanner</li>
        <li>OSS engine, CLI, GitHub Action</li>
        <li>Terms / Privacy / Pricing skeleton for Paddle A3</li>
      </ul>

      <h2>What is deliberately not shipping</h2>
      <ul>
        <li>GitHub OAuth, accounts, Postgres, scheduled monitoring</li>
        <li>Paddle checkout</li>
        <li>Human sales or support</li>
      </ul>

      <p>
        Raw notes and measurement log:{" "}
        <Link href="https://github.com/bistuwangqiyuan/CursorFlowAI/blob/main/product/gate0/EVIDENCE.md">
          product/gate0/EVIDENCE.md
        </Link>
        .
      </p>
    </article>
  );
}
