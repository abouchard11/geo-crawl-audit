# Interpreting Results & Fix Playbook

## Score bands

- **85–100** — GEO-ready. Move budget to content shaping (query fan-out coverage) and off-site entity work.
- **60–84** — Fixable gaps. Usually TTFB or thin HTML. Fixes are days, not months.
- **< 60** — Gated. Something structural (CSR shell, bot blocking) is nullifying all other GEO spend. Fix before any content investment.

## Flag codes → fixes

### `CSR_SHELL` (critical)
Raw HTML has <150 visible words: the page is an app shell rendered by JavaScript. GPTBot, ClaudeBot, PerplexityBot, and the OpenAI/Anthropic/Perplexity retrieval bots do not execute JS — they see nothing. Googlebot (feeding Gemini) is the only major renderer.
**Fix:** Server-side render or prerender. Next.js: move page content to Server Components / `getStaticProps`-style rendering; avoid `"use client"` on content-bearing components. Legacy SPA: add prerendering (e.g., ISR, static export, or an edge prerender for bot UAs — note UA-conditional serving is cloaking-adjacent; prefer serving everyone the rendered HTML).
**Verify:** re-run probe; `visible_words` should jump to full page copy.

### `BOT_DIFFERENTIAL` (critical for retrieval/user-fetch bots)
A bot UA got a different status/size than the browser baseline, or hit a challenge (Cloudflare `cf-mitigated`, Vercel mitigation headers).
**Important:** this proves a bot-sensitive layer exists, not that the real bot is blocked — the probe's IP isn't the bot's. Confirm in logs.
**Fix:** In the WAF/bot-management console (Vercel Firewall, Cloudflare Bot Fight/Super Bot Fight, AWS WAF), add allow rules for the AI crawlers you want. Vercel: check whether the Bot Protection managed ruleset or custom rules are challenging non-browser traffic; explicitly allow verified AI bots. Cloudflare: enable the "verified bots" allowance and check AI Scrapers settings.
**Verify:** logs show 200s for the bot after the change.

### `SLOW_TTFB` / `COLD_START` (high)
Median bot TTFB > 1.2s (or > 2s critical). Bots run aggressive fetch timeouts; slow origins get abandoned mid-request — the log signature is nginx/proxy status **499**. You lose the crawl AND the citation, with no error surfaced anywhere.
Cold-start gap matters more than warm numbers: crawlers disproportionately hit long-tail/uncached pages, so they experience the cold number.
**Fix, in order of leverage:**
1. Cache HTML at the CDN edge (ISR with sensible revalidate; `s-maxage` + `stale-while-revalidate` headers)
2. Kill serverless cold starts on content routes (static generation; or provisioned/edge runtime)
3. Cut origin work before first byte: DB queries, blocking middleware, auth checks on public pages
**Verify:** `x-vercel-cache: HIT` (or `cf-cache-status: HIT`) on probe; cold TTFB converges toward warm.

### `ROBOTS_BLOCKS` (high)
robots.txt disallows an AI bot for root. Decide deliberately per category:
- **Retrieval/user-fetch bots** (OAI-SearchBot, Claude-SearchBot, ChatGPT-User, Claude-User, PerplexityBot, bingbot): blocking these removes you from live AI answers. For a lead-gen site this is nearly always wrong.
- **Training bots** (GPTBot, ClaudeBot, CCBot, meta-externalagent, Google-Extended, Applebot-Extended): a strategy choice — allow for long-term brand presence in models, block to withhold content. For local-service lead-gen, allowing is usually the money-maximizing call.

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
- **Live-citation lever** (retrieval + user-fetch bots): affects AI answers *this month*. Revenue-adjacent for lead-gen.
- **Training lever** (training bots): affects whether future model versions "know" the brand. Compounding, slow, cheap to secure now.

The single most common misread to preempt: "we rank fine in Google, so AI can see us." False — Google renders JS and nothing else does. A site can be #1 in Google and 100% invisible to ChatGPT/Claude/Perplexity retrieval.
