# Interpreting Results & Fix Playbook

## Score bands

- **85–100** — No major issue detected by the heuristic probe.
- **60–84** — Investigate the flagged TTFB, HTML, robots, or response differences.
- **< 60** — Major probe findings. Confirm simulated-UA results with real crawler logs before acting.

If the baseline request is not a normal 200 response, the score is withheld as inconclusive.

## Flag codes → fixes

### `CSR_SHELL` (critical)
The baseline raw HTML has <150 visible words. That is evidence that a non-rendering client may miss client-rendered content; it is not proof that every vendor crawler receives identical HTML or never renders JavaScript. Google documents a Chromium rendering stage for Google Search, while other vendors do not uniformly document rendering behavior.
**Fix:** Server-side render or prerender. Next.js: move page content to Server Components / `getStaticProps`-style rendering; avoid `"use client"` on content-bearing components. Legacy SPA: add prerendering (e.g., ISR, static export, or an edge prerender for bot UAs — note UA-conditional serving is cloaking-adjacent; prefer serving everyone the rendered HTML).
**Verify:** re-run the probe, compare browser and bot-UA response bodies, and confirm real crawler requests in logs.

### `BOT_DIFFERENTIAL` (critical for retrieval/user-fetch bots)
A bot UA got a different status/size than the browser baseline, or hit a challenge (Cloudflare `cf-mitigated`, Vercel mitigation headers).
**Important:** this proves a bot-sensitive layer exists, not that the real bot is blocked — the probe's IP isn't the bot's. Confirm in logs.
**Fix:** In the WAF/bot-management console (Vercel Firewall, Cloudflare Bot Fight/Super Bot Fight, AWS WAF), add allow rules for the AI crawlers you want. Vercel: check whether the Bot Protection managed ruleset or custom rules are challenging non-browser traffic; explicitly allow verified AI bots. Cloudflare: enable the "verified bots" allowance and check AI Scrapers settings.
**Verify:** logs show 200s for the bot after the change.

### `SLOW_TTFB` / `TTFB_VARIANCE` (high)
Median simulated-UA TTFB > 1.2s (or > 2s critical) is an audit heuristic that warrants log review, not a vendor SLA. Status **499** means the client closed the request before the server completed it; correlate it with user agent, path, duration, and upstream logs before assigning a cause.
A large first/repeat gap is a variability signal. Use cache headers and origin traces to determine whether a CDN miss, cold start, or another dependency caused it.
**Fix, in order of leverage:**
1. Cache HTML at the CDN edge (ISR with sensible revalidate; `s-maxage` + `stale-while-revalidate` headers)
2. Kill serverless cold starts on content routes (static generation; or provisioned/edge runtime)
3. Cut origin work before first byte: DB queries, blocking middleware, auth checks on public pages
**Verify:** inspect `x-vercel-cache` (or `cf-cache-status`) and origin traces; repeat measurements from more than one run or location.

### `ROBOTS_BLOCKS` (high)
robots.txt disallows an AI bot for root. Decide deliberately per category:
- **Retrieval/user-fetch bots** (OAI-SearchBot, Claude-SearchBot, ChatGPT-User, Claude-User, PerplexityBot): blocking can reduce or prevent vendor-documented search or user-initiated fetches. Check current vendor policy before deciding.
- **Training bots** (GPTBot, ClaudeBot, CCBot, meta-externalagent, Google-Extended, Applebot-Extended): a strategy and rights choice. Allowing makes collection possible; it does not guarantee training inclusion or model knowledge.

### `THIN_HTML` (warn)
150–400 visible words. Retrievable but weak for passage retrieval — engines select *passages*, and there aren't enough. Expand answer-shaped sections (FAQ blocks, specific data, entity-rich copy).

### `NO_SITEMAP` / `NO_ROBOTS` (warn)
Add them. Retrieval indexes use sitemaps for discovery and freshness the same way search engines do. Ensure `<lastmod>` is real, not build-timestamp noise.

### `IMPLICIT_ALLOW` (info)
Retrieval bots are only allowed via `User-agent: *`. Works today, but explicit blocks are self-documenting, survive future wildcard tightening, and signal deliberate policy. Low effort, do it during the next deploy.

### `NO_LLMS_TXT` (info — deliberately weight-zero)
Evidence as of 2026: the overwhelming majority of llms.txt files receive zero AI crawler requests, and Google states it does nothing for Search. Cheap to add, fine as polish, never a priority. If a client or vendor leads their pitch with llms.txt, treat it as a signal about the vendor.

## Presenting to stakeholders

Frame every finding by which lever it pulls:
- **Retrieval lever** (retrieval + user-fetch bots): affects whether the vendor is permitted and technically able to fetch the page, subject to its product behavior.
- **Training-permission lever** (training bots): affects collection eligibility, not guaranteed dataset inclusion or future model behavior.

The common misread to preempt is: "we rank fine in Google, so every AI crawler receives the same usable page." Google documents JavaScript rendering for Search; that does not establish what another vendor fetches, renders, indexes, or cites. Test the response and confirm with owned logs.
