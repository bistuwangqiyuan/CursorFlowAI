# Gate 0 evidence log — TriadGuard (C12)

**Baseline / tool ship date:** 2026-08-03 (Asia/Shanghai)  
**Candidate:** C12 — AI agent CI/CD configuration security audit  
**Discipline:** B3 fail ⇒ abandon C12 (or retry next candidate ≤2). No hosted SaaS before Gate 0-B + Gate 1.

Raw machine outputs: `hn-b2.json`, `github-b1.json`.

---

## Gate 0-A — Paddle (human)

| ID | Check | Status | Notes |
|----|-------|--------|-------|
| A1 | Mainland China natural person KYC | ⏳ pending | Operator must register at paddle.com |
| A2 | CNY payout bank verified | ⏳ pending | After A1 |
| A3 | Site + Terms + Privacy + Pricing | ✅ shipped | Live site pages under `/legal/*` and `/pricing` |

---

## B1 — Search demand existence

### B1a — Adoption / code presence (GitHub code search, 2026-08-03)

Via authenticated `gh api search/code` (`fetch_b1_gh.mjs`):

| Query | `total_count` |
|-------|---------------|
| `path:.github/workflows anthropics/claude-code-action` | **7488** |
| `path:.github/workflows google-github-actions/run-gemini-cli` | **1142** |
| `path:.github/workflows openai/codex-action` | **888** |
| `path:.github/workflows pull_request_target claude-code-action` | **536** |
| `path:.github/workflows permissions: write-all claude-code-action` | **14** |

**Interpretation:** Agent Actions are widely present; `pull_request_target` co-occurrence with Claude action is non-trivial (536). Exact “fatal triangle” intersection still needs manual sampling (Gate 1 W1).

### B1b — Keyword volume / KD (Ahrefs or Semrush free tier)

**Status: ⏳ not yet executed** (requires operator login to Ahrefs/Semrush free tier).

Candidate keyword family (to be measured; do not treat as verified volume):

1. github actions prompt injection  
2. pull_request_target security  
3. claude code action security  
4. ai agent github actions  
5. github actions ai security  
6. promptpwnd  
7. gitlost github  
8. ci cd ai agent security  

**Pass rule (BP):** family monthly volume ≥ 1000 **and** ≥ 5 terms with KD ≤ 20.  
**Until measured:** B1 is **incomplete** — do not claim SEO demand proven. GitHub adoption (B1a) is a separate signal.

---

## B2 — Community topic heat (HN Algolia, last 12 months)

Script: `fetch_b2_hn.mjs` → `hn-b2.json` (2026-08-03).

| Metric | Value |
|--------|-------|
| Unique stories across 5 queries | **101** |
| Stories with points **> 50** | **10** |

**Pass rule:** ≥ 10 related threads in 12 months **and** ≥ 3 with score > 50.

**Honest relevance filter:** Algolia returns adjacent “AI agent + tooling” posts. Strictly CI/agent-security-adjacent high-score examples include:

- [OneCLI – keep secrets out of AI agents](https://news.ycombinator.com/item?id=49023427) (110 pts)  
- [Context-aware permission guard for Claude Code](https://news.ycombinator.com/item?id=47343927) (127 pts)  
- [Policy enforcement for Claude Code / Cursor / Codex](https://news.ycombinator.com/item?id=48847526) (13 pts)  
- [AgentArmor – security framework for AI agents](https://news.ycombinator.com/item?id=47374958) (10 pts)  
- [gh-slimify – GitHub Actions runner migration](https://news.ycombinator.com/item?id=45936564) (69 pts)

**Provisional B2:** **PASS on quantity** (≥10 threads, ≥3 with >50 pts in the raw set).  
**Caveat:** topical precision is mixed; Reddit cross-check still recommended before claiming “hot category.”

**Reddit:** ⏳ operator spot-check (r/github, r/netsec, r/devops) — not automated in this log.

---

## B3 — Free tool natural distribution (hard gate)

| Field | Value |
|-------|-------|
| Product | TriadGuard free browser scan + CLI + Action |
| Launch URL | https://triadguard.vercel.app (alias → product-dusky-eight.vercel.app) |
| Source commit | https://github.com/bistuwangqiyuan/CursorFlowAI/commit/4cc9123785fad3423cbe724f34a21a566db3718b |
| Launch posts | See `LAUNCH.md` (draft; human posts) |
| Window start | _(UTC date when Show HN + 2 communities posted)_ |
| Window end | start + 14 days |
| UV target | ≥ 300 real unique visitors |
| Uses target | ≥ 30 (browser `scan_completed` + CLI/Action runs) |
| UV actual | _TBD_ |
| Uses actual | _TBD_ |
| **Verdict** | ⏳ observing |

Measurement:

- UV: Vercel Analytics  
- Browser uses: anonymous `scan_completed` + localStorage counter  
- CLI/Action: npm downloads / Action runs (telemetry off by default)

---

## B4 — Compounding channel hypothesis

**Mechanism (concrete):** Each install of the GitHub Action leaves a public line in `.github/workflows/*.yml` referencing `bistuwangqiyuan/CursorFlowAI/product/action@…`, which is indexed by GitHub code search and visible to contributors → installs create discovery surface without ads.

| Observation | Status |
|-------------|--------|
| ≥ 1 spontaneous third-party reference (fork, awesome-list, blog, unrelated README) within B3 window | ⏳ |

---

## Gate 0 verdict (fill on D19)

| Gate | Result | Date |
|------|--------|------|
| 0-A | ⏳ | |
| 0-B B1 | ⏳ incomplete (SEO volume) / B1a strong | |
| 0-B B2 | ✅ provisional pass | 2026-08-03 |
| 0-B B3 | ⏳ | |
| 0-B B4 | ⏳ | |
| **Overall** | ⏳ | |

If B3 fails: abandon C12 commercialization path per `docs/GATE0.md`; do not expand product scope.
