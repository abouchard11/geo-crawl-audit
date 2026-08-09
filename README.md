# geo-crawl-audit

**Can AI actually see your website?** A zero-dependency audit tool that answers the question most SEO stacks can't: whether AI crawlers (GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, and friends) can *reach*, *fetch fast enough*, and *read* your site.

Most GEO/AI-visibility tooling monitors the **output** — "did ChatGPT mention my brand?" This tool audits the **input** — "did the bot successfully retrieve my page?" — which is where most failures actually happen, and the first thing to fix.

## Why this matters

A site can rank well in Google while its baseline HTML is thin, bot policies are restrictive, or real crawler requests fail. Three failure modes worth testing:

| Failure | Mechanism | Who catches it |
|---|---|---|
| **Thin baseline HTML** | Client-rendered content may be absent from the raw HTML response. Vendor rendering behavior is not uniformly documented, so confirm crawler-specific responses and actual logs before concluding what a bot read. | Often missed because the site works in a browser |
| **Slow or cancelled** | Slow TTFB can contribute to timeouts or client cancellations. A 499 is a useful log signal, but it does not by itself identify a crawler timeout or prove a lost citation. | Nobody who isn't reading logs |
| **Blocked** | WAF / bot-management rules (often defaults) challenge or 403 AI crawlers while humans sail through. | Nobody — the block is invisible from a browser |

## Quickstart

Requires Python 3.8+ and `curl`. No pip installs.

```bash
# Audit one or more sites
python3 scripts/geo_probe.py example.com another.com --out ./results

# Or a portfolio
python3 scripts/geo_probe.py --domains-file domains.txt --out ./results
```

Output: `geo_audit_report.md` (scorecard + flags, worst first) and `geo_audit.json`.

### What the probe does per domain

- Fetches with a **baseline browser UA**, then with ~12 real AI crawler UAs
- Measures **first and repeat TTFB** separately. The gap is a variability signal, not proof of a cold start or cache miss.
- Flags **differentials**: any bot treated differently than the browser (status, challenge headers, body size)
- Classifies raw HTML as `SSR_FULL` / `SSR_THIN` / `CSR_SHELL` — visible words **without** JS execution
- Parses robots.txt verdicts for every AI bot token — including **token-only agents** like `Google-Extended` and `Applebot-Extended`, which never fetch (Googlebot/Applebot do) and therefore never appear in your logs; most tools get this wrong
- Checks llms.txt, and deliberately weights it near zero because crawler support and impact are not established enough to make it a primary gate

### Log ground truth (Mode B)

The probe tells you what filtering *exists*; logs tell you what actually *happened* to real crawlers:

```bash
python3 scripts/drain_parser.py logs/*.ndjson --out ./results --verify
```

Parses Vercel Log Drain exports (NDJSON/JSON) or nginx/apache combined logs. Per bot: hits, status distribution (**499s highlighted**), top crawled paths, first/last seen. `--verify` checks client IPs against each vendor's published ranges to split real bots from impostors — anyone can send `User-Agent: GPTBot`, and scrapers constantly do.

See `references/log-pipeline.md` for drain setup (including a Vercel → PostHog route).

## Reading results

- **Score 85–100**: no major issue detected by this heuristic probe
- **60–84**: investigate the flagged TTFB, HTML, robots, or response differences
- **< 60**: major probe findings; confirm simulated-UA results with real crawler logs before acting

If the baseline request is not a normal 200 response, the tool marks the result **inconclusive** and withholds the numeric score.

Full flag-by-flag fix playbook: `references/interpreting.md`.

### The honesty clause (read this)

Probes are sent from *your* machine's IP with simulated bot user-agents. WAFs that verify bots by published IP ranges may treat the simulation differently than the real crawler — **in either direction**. A differential therefore means *"a bot-sensitive filtering layer exists — confirm with logs"*, never "the real bot is definitely blocked." The tool reports it exactly that way. Diagnostic tools that overclaim are worse than no tool.

## Bot registry

`scripts/bots.json` — curated registry of the crawlers that matter, each classified as:

- **retrieval** (OAI-SearchBot, Claude-SearchBot, PerplexityBot…) → vendor-documented search/retrieval crawlers
- **user_fetch** (ChatGPT-User, Claude-User, Perplexity-User…) → in-conversation page fetches
- **training** (GPTBot, ClaudeBot, CCBot, meta-externalagent…) → collection eligibility for training, not guaranteed inclusion or model memory

The distinction matters: blocking a training bot and blocking a search crawler can have different product effects. Follow each vendor's current documentation; an allow rule makes collection possible, not guaranteed. Long-tail bot list maintained by the community at [ai-robots-txt](https://github.com/ai-robots-txt/ai.robots.txt) — this project deliberately doesn't duplicate it.

## Use as a Claude skill

`skill/SKILL.md` packages this as an agent skill for Claude (Claude Code / Cowork): say "run a GEO crawl audit on example.com" and the agent runs both modes and interprets results against the playbook.

## Example

`examples/` contains an archived August 2026 audit run across 18 major sites. It is a reproducibility artifact, not a current claim about any named company's crawler access; rerun the probe and confirm with owned logs before drawing conclusions.

## License

MIT
