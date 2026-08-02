# TriadGuard (Gate 0)

Free, zero-LLM scanner for the **AI agent CI/CD fatal triangle**: untrusted input × agent action × high privilege / exfiltration path.

This directory is the product validation surface for business-plan candidate **C12**. Hosted monitoring SaaS is **out of scope** until Gate 0-B and Gate 1 pass. See [gate0/EVIDENCE.md](gate0/EVIDENCE.md) and [../docs/GATE0.md](../docs/GATE0.md).

## Packages

| Path | Role |
|------|------|
| `packages/engine` | Shared YAML rule engine |
| `packages/cli` | `triadguard` CLI (`npx` / local) |
| `action` | Composite GitHub Action |
| `web` | Next.js site → Vercel |

## Develop

```bash
cd product
npm install
npm test
npm run build
npm run dev          # web on :3000
npm run scan -- ../product/packages/engine/fixtures
```

## GitHub Action

```yaml
- uses: bistuwangqiyuan/CursorFlowAI/product/action@main
  with:
    path: .github/workflows
```

Example workflow copy-paste: [`action/examples/self-check.yml`](action/examples/self-check.yml).

## Deploy (Vercel)

Root directory for the Vercel project should be `product/web` (see `web/vercel.json` install/build commands that build the workspace from `product/`).
