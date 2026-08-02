import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "TriadGuard — AI agent CI config scanner",
    template: "%s · TriadGuard",
  },
  description:
    "Free, zero-LLM scanner for the fatal triangle in CI: untrusted input × AI agent privileges × exfiltration paths. Runs in your browser or CLI.",
  openGraph: {
    title: "TriadGuard",
    description:
      "Scan GitHub Actions workflows for AI agent fatal-triangle risks. Free one-shot scan. Continuous monitoring not yet open.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600;700&family=Syne:wght@700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div className="shell">
          <header className="site-header">
            <Link className="brand" href="/">
              TriadGuard
            </Link>
            <nav className="nav" aria-label="Primary">
              <Link href="/">Scan</Link>
              <Link href="/docs">Docs</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/gate0">Gate 0</Link>
              <Link href="/legal/privacy">Privacy</Link>
            </nav>
          </header>
          <main>{children}</main>
          <footer className="site-footer">
            <p>
              TriadGuard reports configuration risk signals only — it does not certify compliance.
              Findings are always free. No human support at the planned $19–49/mo price.
            </p>
            <p>
              <Link href="/legal/terms">Terms</Link>
              {" · "}
              <Link href="/legal/privacy">Privacy</Link>
              {" · "}
              <a href="https://github.com/bistuwangqiyuan/CursorFlowAI/tree/main/product">
                Source
              </a>
            </p>
          </footer>
        </div>
        <Analytics />
      </body>
    </html>
  );
}
