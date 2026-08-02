# Gate 0 launch checklist (human posts)

AI drafts copy. **A human must post** — do not impersonate a person with an automated account.

## Pre-flight

- [ ] Production URL live (HTTPS)
- [ ] Browser scan works on sample workflow
- [ ] `/pricing`, `/legal/terms`, `/legal/privacy`, `/gate0` reachable
- [ ] Vercel Analytics enabled
- [ ] Record **window start** timestamp in `EVIDENCE.md`

## Channel 1 — Hacker News Show HN

**Title (draft):**  
`Show HN: TriadGuard – scan CI workflows for AI-agent fatal-triangle risks`

**Body (draft):**

```
TriadGuard is a free, zero-LLM scanner for a config pattern showing up in CI:

  untrusted events (e.g. pull_request_target / issue comments)
  × AI agent Actions (Claude Code / Gemini CLI / Codex)
  × high privileges + an egress path

It runs in the browser (YAML never leaves your machine) or as a CLI / GitHub Action.

This is a Gate-0 traffic test from our business plan: if we cannot get ~300 UV
and 30 real uses in 14 days with zero paid ads, we kill the commercial path.

Site: <URL>
Source: https://github.com/bistuwangqiyuan/CursorFlowAI/tree/main/product

Not a compliance cert. Findings are always free.
```

## Channel 2 — vertical community A

Pick one: r/devops, r/github, or r/netsec. Follow subreddit rules; no spam.

## Channel 3 — vertical community B

Pick one: relevant Discord/Slack (e.g. security engineering) or Dev.to short post linking the same URL.

## Hard rules

- No paid ads during the 14-day window  
- No feature expansion — crash fixes only  
- Do not claim “market validated” until B3 numbers are filled
