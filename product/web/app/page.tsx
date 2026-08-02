import { Scanner } from "./components/Scanner";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <p className="badge">Free one-shot scan · zero LLM</p>
        <h1>TriadGuard</h1>
        <p className="lede">
          Detect the fatal triangle in CI: untrusted input flowing into an AI agent that holds high
          privileges and can exfiltrate or mutate. Pure YAML rules — no model calls, no file upload.
        </p>
        <div className="cta-row">
          <a className="btn btn-primary" href="#scanner">
            Scan a workflow
          </a>
          <a className="btn btn-ghost" href="/docs">
            How rules work
          </a>
        </div>
        <pre className="cmd">{`npx triadguard .github/workflows`}</pre>
      </section>
      <div id="scanner">
        <Scanner />
      </div>
    </>
  );
}
