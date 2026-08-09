---
name: geo-crawl-audit
description: Audit whether AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, etc.) can actually reach, fetch, and read a website — the technical gate for GEO / AI search visibility. Probes sites with real bot user-agents, measures TTFB and WAF/bot-management differentials, verifies content exists in raw HTML without JavaScript, parses robots.txt AI-bot handling, and analyzes server logs for per-bot traffic, 499 abandons, and impostor bots. Use this whenever the user asks about GEO, AEO, AI visibility, AI crawlers, bot access, "can ChatGPT/Claude/Perplexity see my site", 499 errors, AI bot traffic in logs, llms.txt, whether a WAF is blocking AI bots, or wants an AI-search technical audit of one site or a whole portfolio — even if they only say "check my site for AI search" or "why isn't my site cited by AI".
---

# GEO Crawl Audit

Diagnose the **input side** of AI search visibility: whether AI crawlers can reach a site, how fast it serves them, and whether they can read it without executing JavaScript. Most GEO tooling monitors the *output* (are we mentioned in AI answers?); this skill audits the *input* (did the bot successfully fetch us?) — which is where most failures actually happen and the first thing to fix.

## Why this ordering matters

An AI engine can only cite what it successfully retrieved. The failure chain, in order:
1. **Reachability** — WAF/bot-management silently 403s or challenges the crawler
2. **Speed** — slow TTFB makes the bot abandon (logged as 499, invisible in analytics)
3. **Raw-HTML readability** — client-rendered content may be absent from a non-rendering response; vendor rendering behavior is not uniformly documented, so confirm with bot-specific responses and real logs
4. **Permission** — robots.txt tokens (incl. token-only entries like Google-Extended that never fetch but control training use)

Never recommend content or "AI optimization" work before these gates pass. It's optimizing retrieval for a bot that isn't reaching the page.

## Mode A — Active probe (no setup, run anytime)

```bash
python3 scripts/geo_probe.py example.com other.com --out ./audit-results
# or: --domains-file domains.txt
```

Produces `geo_audit_report.md` (scorecard + flags, worst-first) and `geo_audit.json`. Per domain it:
- probes the homepage with ~12 real bot UAs + a baseline browser UA
- measures first and repeat TTFB as a variability signal, without assuming either request is a cache miss or cold start
- flags **differentials**: any bot UA treated differently than the browser
- classifies raw HTML as SSR_FULL / SSR_THIN / CSR_SHELL (visible words without JS)
- parses robots.txt verdicts for every AI bot token, including token-only agents
- checks llms.txt (informational only — evidence says near-zero impact; never lead with it)

**Interpretation rules — read before presenting results:**
- A differential means "a bot-sensitive filtering layer exists", NOT "the real bot is blocked". Probes come from this machine's IP; WAFs doing verified-bot IP checks may treat the simulation differently in either direction. Present it as a lead to confirm in logs (Mode B).
- CSR_SHELL means the baseline raw HTML is thin. State that non-rendering clients may miss content, then compare bot-UA bodies and real logs; do not claim every vendor sees nothing.
- Median simulated-UA TTFB > 1.2s is an audit heuristic, not a vendor SLA. Treat a first/repeat gap as a variability lead and use cache headers or origin traces to identify the cause. A 499 means client cancellation, not automatically a crawler timeout or lost citation.
- Retrieval + user_fetch categories represent vendor-documented retrieval paths; training categories represent collection permission. Do not promise citations, training inclusion, model memory, or timing from an allow rule.

For threshold rationale and the fix playbook (per flag code), read `references/interpreting.md`.

## Mode B — Log ground truth

```bash
python3 scripts/drain_parser.py logs/*.ndjson --out ./audit-results --verify
```

Parses Vercel Log Drain exports (NDJSON/JSON) or nginx/apache combined logs. Reports per-bot hits, status distribution (499s highlighted), top crawled paths, first/last seen, and `--verify` checks client IPs against each vendor's published ranges to split real bots from impostors.

No drain set up yet? Read `references/log-pipeline.md` — includes the Vercel Drains → PostHog route (query with HogQL via the PostHog MCP if connected) and the plain file-drain route. Vercel runtime logs alone are NOT sufficient: they miss static/edge requests, which is most bot traffic.

"No AI bot traffic found" is itself a finding: either the logs don't cover edge requests, or the site has an awareness problem upstream of any technical fix.

## Workflow

1. Run Mode A across all target domains (get them from the user, a domains file, or their hosting provider's project list).
2. Present the scorecard worst-first; lead with CRITICAL flags. Keep the llms.txt result to a footnote.
3. For any differential or slow-TTFB flag, run or set up Mode B to confirm what real bots experience.
4. Translate each confirmed finding into its fix (see `references/interpreting.md`) and state whether it affects retrieval access or training collection eligibility.
5. Re-run Mode A after fixes ship; compare scores.

## Maintenance

The bot registry lives in `scripts/bots.json` (curated: UA strings, category, IP-range URLs, probe eligibility). The long-tail blocklist world is already maintained by the community — refresh candidates from `https://raw.githubusercontent.com/ai-robots-txt/ai.robots.txt/main/robots.json` (MIT) rather than hand-tracking new bots. Vendor UA strings and IP-range URLs change; if a probe suddenly 404s or a verify source fails, check the vendor's bot documentation page first.
