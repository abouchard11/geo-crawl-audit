# GEO Crawl Audit

> **Archived snapshot:** this is unedited v0.1 probe output from one network location on 2026-08-07. Simulated user-agent results can differ from real verified crawlers, site behavior changes, and several conclusions use wording superseded by the current tool. Treat it as a reproducibility artifact—not a current claim about any named company. Rerun and confirm with owned logs.

**Generated:** 2026-08-07 11:22 UTC  
**Method:** active multi-UA probe (see caveat at bottom)

## Portfolio scorecard

| Domain | Score | Raw HTML | Words | Warm TTFB | Cold TTFB | Bot TTFB (med) | Differentials | Sitemap |
|---|---|---|---|---|---|---|---|---|
| reddit.com | **32** | CSR_SHELL | 1 | 0.211s | 1.109s | 0.203s | 5 | ✗ |
| airbnb.com | **35** | CSR_SHELL | 94 | 0.477s | 0.694s | 0.364s | 9 | ✓ |
| quora.com | **52** | CSR_SHELL | 9 | 0.198s | 0.57s | 0.3s | 12 | ✗ |
| theguardian.com | **55** | SSR_FULL | 3314 | 0.388s | 1.38s | 0.236s | 8 | ✓ |
| nytimes.com | **55** | SSR_FULL | 1222 | 0.357s | 1.447s | 0.298s | 10 | ✓ |
| openai.com | **60** | CSR_SHELL | 6 | 0.21s | 0.264s | 0.227s | 12 | ✓ |
| perplexity.ai | **60** | CSR_SHELL | 9 | 0.214s | 0.572s | 0.207s | 12 | ✓ |
| linkedin.com | **72** | CSR_SHELL | 23 | 0.22s | 0.233s | 0.217s | — | ✗ |
| notion.so | **75** | SSR_FULL | 627 | 0.677s | 1.23s | 0.597s | 2 | ✓ |
| wikipedia.org | **80** | SSR_FULL | 868 | 0.282s | 0.67s | 0.264s | 3 | ✓ |
| bloomberg.com | **95** | CSR_SHELL | 108 | 0.377s | 1.475s | 0.303s | — | ✓ |
| github.com | **95** | CSR_SHELL | 6 | 0.147s | 0.115s | 0.203s | — | ✗ |
| figma.com | **95** | SSR_FULL | 591 | 0.969s | 2.459s | 0.203s | — | ✓ |
| shopify.com | **97** | SSR_FULL | 1226 | 0.222s | 0.493s | 0.24s | — | ✗ |
| stripe.com | **100** | SSR_FULL | 1957 | 0.561s | 0.25s | 0.317s | — | ✓ |
| vercel.com | **100** | SSR_FULL | 539 | 0.352s | 0.531s | 0.25s | — | ✓ |
| developer.mozilla.org | **100** | SSR_FULL | 1134 | 0.323s | 0.63s | 0.271s | — | ✓ |
| anthropic.com | **100** | SSR_FULL | 677 | 0.102s | 0.202s | 0.093s | — | ✓ |

## Flags (worst first)

- **[CRITICAL] reddit.com** `BOT_DIFFERENTIAL` — ChatGPT-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] reddit.com** `BOT_DIFFERENTIAL` — bingbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] reddit.com** `CSR_SHELL` — only 1 visible words in raw HTML — invisible to non-JS AI crawlers
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — OAI-SearchBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — ChatGPT-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — PerplexityBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — Perplexity-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — bingbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `BOT_DIFFERENTIAL` — Amazonbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] airbnb.com** `CSR_SHELL` — only 94 visible words in raw HTML — invisible to non-JS AI crawlers
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — OAI-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — ChatGPT-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — Claude-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — Claude-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — PerplexityBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — Perplexity-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — bingbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] quora.com** `BOT_DIFFERENTIAL` — Amazonbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] theguardian.com** `BOT_DIFFERENTIAL` — Claude-SearchBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] theguardian.com** `BOT_DIFFERENTIAL` — Claude-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] theguardian.com** `BOT_DIFFERENTIAL` — PerplexityBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] theguardian.com** `BOT_DIFFERENTIAL` — Perplexity-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] theguardian.com** `BOT_DIFFERENTIAL` — Amazonbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — OAI-SearchBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — ChatGPT-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — Claude-SearchBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — Claude-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — PerplexityBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] nytimes.com** `BOT_DIFFERENTIAL` — Perplexity-User: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — OAI-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — ChatGPT-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — Claude-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — Claude-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — PerplexityBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — Perplexity-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — bingbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] openai.com** `BOT_DIFFERENTIAL` — Amazonbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — OAI-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — ChatGPT-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — Claude-SearchBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — Claude-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — PerplexityBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — Perplexity-User: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — bingbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] perplexity.ai** `BOT_DIFFERENTIAL` — Amazonbot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] linkedin.com** `CSR_SHELL` — only 23 visible words in raw HTML — invisible to non-JS AI crawlers
- **[CRITICAL] notion.so** `BOT_DIFFERENTIAL` — bingbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] notion.so** `BOT_DIFFERENTIAL` — Amazonbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[CRITICAL] wikipedia.org** `BOT_DIFFERENTIAL` — bingbot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] reddit.com** `BOT_DIFFERENTIAL` — GPTBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] reddit.com** `BOT_DIFFERENTIAL` — ClaudeBot: status 429 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] reddit.com** `BOT_DIFFERENTIAL` — CCBot: status 429 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] reddit.com** `ROBOTS_BLOCKS` — robots.txt blocks: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, bingbot, Amazonbot, CCBot, meta-externalagent, Google-Extended, Applebot-Extended
- **[HIGH] airbnb.com** `BOT_DIFFERENTIAL` — GPTBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] airbnb.com** `BOT_DIFFERENTIAL` — CCBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] airbnb.com** `BOT_DIFFERENTIAL` — meta-externalagent: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] quora.com** `BOT_DIFFERENTIAL` — GPTBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] quora.com** `BOT_DIFFERENTIAL` — ClaudeBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] quora.com** `BOT_DIFFERENTIAL` — CCBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] quora.com** `BOT_DIFFERENTIAL` — meta-externalagent: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] quora.com** `ROBOTS_BLOCKS` — robots.txt blocks: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, bingbot, CCBot, meta-externalagent, Applebot-Extended
- **[HIGH] theguardian.com** `BOT_DIFFERENTIAL` — ClaudeBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] theguardian.com** `BOT_DIFFERENTIAL` — CCBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] theguardian.com** `BOT_DIFFERENTIAL` — meta-externalagent: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] theguardian.com** `ROBOTS_BLOCKS` — robots.txt blocks: ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Amazonbot, CCBot, meta-externalagent, Applebot-Extended
- **[HIGH] nytimes.com** `BOT_DIFFERENTIAL` — GPTBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] nytimes.com** `BOT_DIFFERENTIAL` — ClaudeBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] nytimes.com** `BOT_DIFFERENTIAL` — CCBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] nytimes.com** `BOT_DIFFERENTIAL` — meta-externalagent: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] nytimes.com** `ROBOTS_BLOCKS` — robots.txt blocks: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, CCBot, meta-externalagent, Google-Extended, Applebot-Extended
- **[HIGH] openai.com** `BOT_DIFFERENTIAL` — GPTBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] openai.com** `BOT_DIFFERENTIAL` — ClaudeBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] openai.com** `BOT_DIFFERENTIAL` — CCBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] openai.com** `BOT_DIFFERENTIAL` — meta-externalagent: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] perplexity.ai** `BOT_DIFFERENTIAL` — GPTBot: cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] perplexity.ai** `BOT_DIFFERENTIAL` — ClaudeBot: cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] perplexity.ai** `BOT_DIFFERENTIAL` — CCBot: cloudflare-challenge,cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] perplexity.ai** `BOT_DIFFERENTIAL` — meta-externalagent: cloudflare-403 — bot-sensitive filtering; confirm with logs
- **[HIGH] notion.so** `ROBOTS_BLOCKS` — robots.txt blocks: Amazonbot
- **[HIGH] wikipedia.org** `BOT_DIFFERENTIAL` — ClaudeBot: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] wikipedia.org** `BOT_DIFFERENTIAL` — meta-externalagent: status 403 vs baseline 200 — bot-sensitive filtering; confirm with logs
- **[HIGH] bloomberg.com** `ROBOTS_BLOCKS` — robots.txt blocks: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, Claude-User, PerplexityBot, Amazonbot, CCBot, meta-externalagent, Google-Extended, Applebot-Extended
- **[HIGH] figma.com** `COLD_START` — cold TTFB 2.459s vs warm 0.969s — bots hitting uncached pages get the cold number
- **[HIGH] figma.com** `ROBOTS_BLOCKS` — robots.txt blocks: GPTBot, OAI-SearchBot, ChatGPT-User, Claude-SearchBot, PerplexityBot, CCBot, Google-Extended
- **[WARN] reddit.com** `NO_SITEMAP` — no Sitemap: line in robots.txt
- **[WARN] quora.com** `BASELINE_ANOMALY` — baseline browser fetch returned 403 — results likely reflect probe-environment filtering, not real bot experience; re-run from a residential network before concluding anything
- **[WARN] quora.com** `NO_SITEMAP` — no Sitemap: line in robots.txt
- **[WARN] openai.com** `BASELINE_ANOMALY` — baseline browser fetch returned 403 — results likely reflect probe-environment filtering, not real bot experience; re-run from a residential network before concluding anything
- **[WARN] perplexity.ai** `BASELINE_ANOMALY` — baseline browser fetch returned 403 — results likely reflect probe-environment filtering, not real bot experience; re-run from a residential network before concluding anything
- **[WARN] linkedin.com** `NO_SITEMAP` — no Sitemap: line in robots.txt
- **[WARN] bloomberg.com** `BASELINE_ANOMALY` — baseline browser fetch returned 403 — results likely reflect probe-environment filtering, not real bot experience; re-run from a residential network before concluding anything
- **[WARN] github.com** `BASELINE_ANOMALY` — baseline browser fetch returned 400 — results likely reflect probe-environment filtering, not real bot experience; re-run from a residential network before concluding anything
- **[WARN] github.com** `NO_ROBOTS` — robots.txt missing or erroring
- **[WARN] shopify.com** `NO_SITEMAP` — no Sitemap: line in robots.txt

## Per-domain detail

### reddit.com — 32/100

- Final URL: https://www.reddit.com/ · server: `snooserv` · cache: `None`
- Title: 'Reddit' · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 0

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.485s | status 403 vs baseline 200 |
| OAI-SearchBot | retrieval | 200 | 0.197s | — |
| ChatGPT-User | user_fetch | 403 | 0.182s | status 403 vs baseline 200 |
| ClaudeBot | training | 429 | 0.204s | status 429 vs baseline 200 |
| Claude-SearchBot | retrieval | 200 | 0.28s | — |
| Claude-User | user_fetch | 200 | 0.202s | — |
| PerplexityBot | retrieval | 200 | 0.247s | — |
| Perplexity-User | user_fetch | 200 | 0.189s | — |
| bingbot | retrieval | 403 | 0.201s | status 403 vs baseline 200 |
| Amazonbot | retrieval | 200 | 0.369s | — |
| CCBot | training | 429 | 0.288s | status 429 vs baseline 200 |
| meta-externalagent | training | 200 | 0.189s | — |

### airbnb.com — 35/100

- Final URL: https://www.airbnb.com/ · server: `nginx` · cache: `None`
- Title: 'Airbnb: Vacation Rentals, Cabins, Beach Houses, Unique Homes & Experiences' · H1: 'Airbnb homepage' · JSON-LD blocks: 1
- llms.txt: no · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.498s | status 403 vs baseline 200 |
| OAI-SearchBot | retrieval | 403 | 0.278s | status 403 vs baseline 200 |
| ChatGPT-User | user_fetch | 403 | 0.361s | status 403 vs baseline 200 |
| ClaudeBot | training | 200 | 0.523s | — |
| Claude-SearchBot | retrieval | 200 | 0.485s | — |
| Claude-User | user_fetch | 200 | 0.438s | — |
| PerplexityBot | retrieval | 403 | 0.358s | status 403 vs baseline 200 |
| Perplexity-User | user_fetch | 403 | 0.426s | status 403 vs baseline 200 |
| bingbot | retrieval | 403 | 0.323s | status 403 vs baseline 200 |
| Amazonbot | retrieval | 403 | 0.309s | status 403 vs baseline 200 |
| CCBot | training | 403 | 0.304s | status 403 vs baseline 200 |
| meta-externalagent | training | 403 | 0.368s | status 403 vs baseline 200 |

### quora.com — 52/100

- Final URL: https://www.quora.com/ · server: `cloudflare` · cache: `None`
- Title: 'Just a moment...' · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 0

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.288s | cloudflare-challenge,cloudflare-403 |
| OAI-SearchBot | retrieval | 403 | 0.315s | cloudflare-challenge,cloudflare-403 |
| ChatGPT-User | user_fetch | 403 | 0.503s | cloudflare-challenge,cloudflare-403 |
| ClaudeBot | training | 403 | 0.224s | cloudflare-challenge,cloudflare-403 |
| Claude-SearchBot | retrieval | 403 | 0.398s | cloudflare-challenge,cloudflare-403 |
| Claude-User | user_fetch | 403 | 0.515s | cloudflare-challenge,cloudflare-403 |
| PerplexityBot | retrieval | 403 | 0.313s | cloudflare-challenge,cloudflare-403 |
| Perplexity-User | user_fetch | 403 | 0.276s | cloudflare-challenge,cloudflare-403 |
| bingbot | retrieval | 403 | 0.584s | cloudflare-challenge,cloudflare-403 |
| Amazonbot | retrieval | 403 | 0.191s | cloudflare-challenge,cloudflare-403 |
| CCBot | training | 403 | 0.26s | cloudflare-challenge,cloudflare-403 |
| meta-externalagent | training | 403 | 0.19s | cloudflare-challenge,cloudflare-403 |

### theguardian.com — 55/100

- Final URL: https://www.theguardian.com/us · server: `None` · cache: `None`
- Title: 'Latest news, sport and opinion from the Guardian' · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 2

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.332s | — |
| OAI-SearchBot | retrieval | 200 | 0.242s | — |
| ChatGPT-User | user_fetch | 200 | 0.206s | — |
| ClaudeBot | training | 403 | 0.236s | status 403 vs baseline 200 |
| Claude-SearchBot | retrieval | 403 | 0.241s | status 403 vs baseline 200 |
| Claude-User | user_fetch | 403 | 0.258s | status 403 vs baseline 200 |
| PerplexityBot | retrieval | 403 | 0.204s | status 403 vs baseline 200 |
| Perplexity-User | user_fetch | 403 | 0.219s | status 403 vs baseline 200 |
| bingbot | retrieval | 200 | 0.236s | — |
| Amazonbot | retrieval | 403 | 0.189s | status 403 vs baseline 200 |
| CCBot | training | 403 | 0.263s | status 403 vs baseline 200 |
| meta-externalagent | training | 403 | 0.228s | status 403 vs baseline 200 |

### nytimes.com — 55/100

- Final URL: https://www.nytimes.com/ · server: `envoy` · cache: `None`
- Title: 'The New York Times - Breaking News, US News, World News and Videos' · H1: 'New York Times - Top Stories' · JSON-LD blocks: 2
- llms.txt: no · sitemaps: 25

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.286s | status 403 vs baseline 200 |
| OAI-SearchBot | retrieval | 403 | 0.387s | status 403 vs baseline 200 |
| ChatGPT-User | user_fetch | 403 | 0.206s | status 403 vs baseline 200 |
| ClaudeBot | training | 403 | 0.298s | status 403 vs baseline 200 |
| Claude-SearchBot | retrieval | 403 | 0.28s | status 403 vs baseline 200 |
| Claude-User | user_fetch | 403 | 0.215s | status 403 vs baseline 200 |
| PerplexityBot | retrieval | 403 | 0.387s | status 403 vs baseline 200 |
| Perplexity-User | user_fetch | 403 | 0.444s | status 403 vs baseline 200 |
| bingbot | retrieval | 200 | 0.299s | — |
| Amazonbot | retrieval | 200 | 0.394s | — |
| CCBot | training | 403 | 0.431s | status 403 vs baseline 200 |
| meta-externalagent | training | 403 | 0.244s | status 403 vs baseline 200 |

### openai.com — 60/100

- Final URL: https://openai.com/ · server: `cloudflare` · cache: `None`
- Title: None · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.234s | cloudflare-challenge,cloudflare-403 |
| OAI-SearchBot | retrieval | 403 | 0.228s | cloudflare-challenge,cloudflare-403 |
| ChatGPT-User | user_fetch | 403 | 0.211s | cloudflare-challenge,cloudflare-403 |
| ClaudeBot | training | 403 | 0.226s | cloudflare-challenge,cloudflare-403 |
| Claude-SearchBot | retrieval | 403 | 0.249s | cloudflare-challenge,cloudflare-403 |
| Claude-User | user_fetch | 403 | 0.229s | cloudflare-challenge,cloudflare-403 |
| PerplexityBot | retrieval | 403 | 0.193s | cloudflare-challenge,cloudflare-403 |
| Perplexity-User | user_fetch | 403 | 0.214s | cloudflare-challenge,cloudflare-403 |
| bingbot | retrieval | 403 | 0.229s | cloudflare-challenge,cloudflare-403 |
| Amazonbot | retrieval | 403 | 0.2s | cloudflare-challenge,cloudflare-403 |
| CCBot | training | 403 | 0.235s | cloudflare-challenge,cloudflare-403 |
| meta-externalagent | training | 403 | 0.201s | cloudflare-challenge,cloudflare-403 |

### perplexity.ai — 60/100

- Final URL: https://www.perplexity.ai/ · server: `cloudflare` · cache: `None`
- Title: 'Just a moment...' · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 2

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.276s | cloudflare-403 |
| OAI-SearchBot | retrieval | 403 | 0.341s | cloudflare-challenge,cloudflare-403 |
| ChatGPT-User | user_fetch | 403 | 0.252s | cloudflare-challenge,cloudflare-403 |
| ClaudeBot | training | 403 | 0.204s | cloudflare-403 |
| Claude-SearchBot | retrieval | 403 | 0.338s | cloudflare-challenge,cloudflare-403 |
| Claude-User | user_fetch | 403 | 0.195s | cloudflare-challenge,cloudflare-403 |
| PerplexityBot | retrieval | 403 | 0.21s | cloudflare-challenge,cloudflare-403 |
| Perplexity-User | user_fetch | 403 | 0.187s | cloudflare-challenge,cloudflare-403 |
| bingbot | retrieval | 403 | 0.2s | cloudflare-challenge,cloudflare-403 |
| Amazonbot | retrieval | 403 | 0.193s | cloudflare-challenge,cloudflare-403 |
| CCBot | training | 403 | 0.187s | cloudflare-challenge,cloudflare-403 |
| meta-externalagent | training | 403 | 0.282s | cloudflare-403 |

### linkedin.com — 72/100

- Final URL: https://linkedin.com/ · server: `ESF` · cache: `None`
- Title: 'Checking your browser - reCAPTCHA' · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 0

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.22s | — |
| OAI-SearchBot | retrieval | 200 | 0.188s | — |
| ChatGPT-User | user_fetch | 200 | 0.252s | — |
| ClaudeBot | training | 200 | 0.175s | — |
| Claude-SearchBot | retrieval | 200 | 0.195s | — |
| Claude-User | user_fetch | 200 | 0.214s | — |
| PerplexityBot | retrieval | 200 | 0.23s | — |
| Perplexity-User | user_fetch | 200 | 0.486s | — |
| bingbot | retrieval | 200 | 0.858s | — |
| Amazonbot | retrieval | 200 | 0.211s | — |
| CCBot | training | 200 | 0.204s | — |
| meta-externalagent | training | 200 | 0.435s | — |

### notion.so — 75/100

- Final URL: https://www.notion.com/ · server: `cloudflare` · cache: `MISS`
- Title: 'The AI workspace that works for you. | Notion' · H1: 'Where teams and agents Think together.' · JSON-LD blocks: 0
- llms.txt: yes · sitemaps: 11

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.592s | — |
| OAI-SearchBot | retrieval | 200 | 0.911s | — |
| ChatGPT-User | user_fetch | 200 | 0.601s | — |
| ClaudeBot | training | 200 | 0.442s | — |
| Claude-SearchBot | retrieval | 200 | 0.553s | — |
| Claude-User | user_fetch | 200 | 0.72s | — |
| PerplexityBot | retrieval | 200 | 0.749s | — |
| Perplexity-User | user_fetch | 200 | 0.684s | — |
| bingbot | retrieval | 403 | 0.222s | status 403 vs baseline 200 |
| Amazonbot | retrieval | 403 | 0.223s | status 403 vs baseline 200 |
| CCBot | training | 200 | 0.925s | — |
| meta-externalagent | training | 200 | 0.465s | — |

### wikipedia.org — 80/100

- Final URL: https://www.wikipedia.org/ · server: `ATS/9.2.13` · cache: `None`
- Title: 'Wikipedia' · H1: 'Wikipedia\n\nThe Free Encyclopedia' · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.262s | — |
| OAI-SearchBot | retrieval | 200 | 0.298s | — |
| ChatGPT-User | user_fetch | 200 | 0.289s | — |
| ClaudeBot | training | 403 | 0.307s | status 403 vs baseline 200 |
| Claude-SearchBot | retrieval | 200 | 0.265s | — |
| Claude-User | user_fetch | 200 | 0.275s | — |
| PerplexityBot | retrieval | 200 | 0.263s | — |
| Perplexity-User | user_fetch | 200 | 0.217s | — |
| bingbot | retrieval | 403 | 0.297s | status 403 vs baseline 200 |
| Amazonbot | retrieval | 200 | 0.224s | — |
| CCBot | training | 200 | 0.237s | — |
| meta-externalagent | training | 403 | 0.192s | status 403 vs baseline 200 |

### bloomberg.com — 95/100

- Final URL: https://www.bloomberg.com/ · server: `Varnish` · cache: `None`
- Title: 'Bloomberg - Are you a robot?' · H1: 'Bloomberg' · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 10

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 403 | 0.291s | — |
| OAI-SearchBot | retrieval | 403 | 0.239s | — |
| ChatGPT-User | user_fetch | 403 | 0.291s | — |
| ClaudeBot | training | 403 | 0.303s | — |
| Claude-SearchBot | retrieval | 403 | 0.309s | — |
| Claude-User | user_fetch | 403 | 0.393s | — |
| PerplexityBot | retrieval | 403 | 0.303s | — |
| Perplexity-User | user_fetch | 403 | 0.389s | — |
| bingbot | retrieval | 403 | 0.253s | — |
| Amazonbot | retrieval | 403 | 0.267s | — |
| CCBot | training | 403 | 0.346s | — |
| meta-externalagent | training | 403 | 0.318s | — |

### github.com — 95/100

- Final URL: https://github.com/ · server: `None` · cache: `None`
- Title: None · H1: None · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 0

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 400 | 0.117s | — |
| OAI-SearchBot | retrieval | 400 | 0.276s | — |
| ChatGPT-User | user_fetch | 400 | 0.119s | — |
| ClaudeBot | training | 400 | 0.273s | — |
| Claude-SearchBot | retrieval | 400 | 0.247s | — |
| Claude-User | user_fetch | 400 | 0.258s | — |
| PerplexityBot | retrieval | 400 | 0.14s | — |
| Perplexity-User | user_fetch | 400 | 0.356s | — |
| bingbot | retrieval | 400 | 0.283s | — |
| Amazonbot | retrieval | 400 | 0.134s | — |
| CCBot | training | 400 | 0.158s | — |
| meta-externalagent | training | 400 | 0.121s | — |

### figma.com — 95/100

- Final URL: https://www.figma.com/ · server: `None` · cache: `None`
- Title: 'Figma: The collaborative canvas for design, code, and AI' · H1: 'The intelligent canvas for infinite creativity' · JSON-LD blocks: 1
- llms.txt: no · sitemaps: 3

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.363s | — |
| OAI-SearchBot | retrieval | 200 | 0.525s | — |
| ChatGPT-User | user_fetch | 200 | 0.693s | — |
| ClaudeBot | training | 200 | 0.441s | — |
| Claude-SearchBot | retrieval | 200 | 0.21s | — |
| Claude-User | user_fetch | 200 | 0.196s | — |
| PerplexityBot | retrieval | 200 | 0.177s | — |
| Perplexity-User | user_fetch | 200 | 0.18s | — |
| bingbot | retrieval | 200 | 0.174s | — |
| Amazonbot | retrieval | 200 | 0.181s | — |
| CCBot | training | 200 | 0.19s | — |
| meta-externalagent | training | 200 | 0.406s | — |

### shopify.com — 97/100

- Final URL: https://www.shopify.com/ · server: `cloudflare` · cache: `BYPASS`
- Title: 'Shopify: The All-in-One Commerce Platform for Businesses - Shopify' · H1: 'Be the nextAI all-star' · JSON-LD blocks: 1
- llms.txt: yes · sitemaps: 0

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.271s | — |
| OAI-SearchBot | retrieval | 200 | 0.238s | — |
| ChatGPT-User | user_fetch | 200 | 0.271s | — |
| ClaudeBot | training | 200 | 0.244s | — |
| Claude-SearchBot | retrieval | 200 | 0.234s | — |
| Claude-User | user_fetch | 200 | 0.298s | — |
| PerplexityBot | retrieval | 200 | 0.21s | — |
| Perplexity-User | user_fetch | 200 | 0.242s | — |
| bingbot | retrieval | 200 | 0.245s | — |
| Amazonbot | retrieval | 200 | 0.22s | — |
| CCBot | training | 200 | 0.232s | — |
| meta-externalagent | training | 200 | 0.224s | — |

### stripe.com — 100/100

- Final URL: https://stripe.com/ · server: `nginx` · cache: `None`
- Title: 'Stripe | Financial Infrastructure to Grow Your Revenue' · H1: 'Financial infrastructure to grow your revenue. Accept payments, offer financial services, and implement custom revenue m' · JSON-LD blocks: 1
- llms.txt: yes · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.821s | — |
| OAI-SearchBot | retrieval | 200 | 0.332s | — |
| ChatGPT-User | user_fetch | 200 | 0.326s | — |
| ClaudeBot | training | 200 | 0.225s | — |
| Claude-SearchBot | retrieval | 200 | 0.308s | — |
| Claude-User | user_fetch | 200 | 0.341s | — |
| PerplexityBot | retrieval | 200 | 0.734s | — |
| Perplexity-User | user_fetch | 200 | 0.248s | — |
| bingbot | retrieval | 200 | 0.243s | — |
| Amazonbot | retrieval | 200 | 0.216s | — |
| CCBot | training | 200 | 0.238s | — |
| meta-externalagent | training | 200 | 0.488s | — |

### vercel.com — 100/100

- Final URL: https://vercel.com/ · server: `Vercel` · cache: `HIT`
- Title: 'Agentic Infrastructure - Vercel' · H1: 'Agentic Infrastructure' · JSON-LD blocks: 1
- llms.txt: yes · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.529s | — |
| OAI-SearchBot | retrieval | 200 | 0.222s | — |
| ChatGPT-User | user_fetch | 200 | 0.625s | — |
| ClaudeBot | training | 200 | 0.221s | — |
| Claude-SearchBot | retrieval | 200 | 0.256s | — |
| Claude-User | user_fetch | 200 | 0.249s | — |
| PerplexityBot | retrieval | 200 | 0.246s | — |
| Perplexity-User | user_fetch | 200 | 0.216s | — |
| bingbot | retrieval | 200 | 0.313s | — |
| Amazonbot | retrieval | 200 | 0.311s | — |
| CCBot | training | 200 | 0.251s | — |
| meta-externalagent | training | 200 | 0.228s | — |

### developer.mozilla.org — 100/100

- Final URL: https://developer.mozilla.org/en-US/ · server: `Google Frontend` · cache: `None`
- Title: 'MDN Web Docs' · H1: 'Resources for Developers, by Developers' · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.297s | — |
| OAI-SearchBot | retrieval | 200 | 0.23s | — |
| ChatGPT-User | user_fetch | 200 | 0.292s | — |
| ClaudeBot | training | 200 | 0.281s | — |
| Claude-SearchBot | retrieval | 200 | 0.26s | — |
| Claude-User | user_fetch | 200 | 0.398s | — |
| PerplexityBot | retrieval | 200 | 0.242s | — |
| Perplexity-User | user_fetch | 200 | 0.233s | — |
| bingbot | retrieval | 200 | 0.19s | — |
| Amazonbot | retrieval | 200 | 0.308s | — |
| CCBot | training | 200 | 0.255s | — |
| meta-externalagent | training | 200 | 0.31s | — |

### anthropic.com — 100/100

- Final URL: https://www.anthropic.com/ · server: `cloudflare` · cache: `DYNAMIC`
- Title: 'Home \\ Anthropic' · H1: 'AI research and products that put safety at the frontier' · JSON-LD blocks: 0
- llms.txt: no · sitemaps: 1

| Bot | Cat | Status | TTFB | Differential |
|---|---|---|---|---|
| GPTBot | training | 200 | 0.093s | — |
| OAI-SearchBot | retrieval | 200 | 0.094s | — |
| ChatGPT-User | user_fetch | 200 | 0.149s | — |
| ClaudeBot | training | 200 | 0.087s | — |
| Claude-SearchBot | retrieval | 200 | 0.107s | — |
| Claude-User | user_fetch | 200 | 0.109s | — |
| PerplexityBot | retrieval | 200 | 0.093s | — |
| Perplexity-User | user_fetch | 200 | 0.088s | — |
| bingbot | retrieval | 200 | 0.103s | — |
| Amazonbot | retrieval | 200 | 0.09s | — |
| CCBot | training | 200 | 0.101s | — |
| meta-externalagent | training | 200 | 0.093s | — |


---
### Method caveat
Probes are sent from this machine's IP with simulated bot user-agents. WAFs that verify bots by IP range may treat the simulation differently than the real crawler (in either direction). A differential here means *a bot-sensitive filtering layer exists* — confirm actual bot outcomes with server logs via `drain_parser.py`.
