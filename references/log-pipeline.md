# Getting Ground-Truth Bot Logs

Active probing shows what filtering exists; only logs show what real bots experienced. Two routes, pick per stack.

## Route 1 — Vercel Drains (covers static + edge + function requests)

Vercel **runtime logs** (dashboard / `get_runtime_logs`) only cover function invocations and have short retention — they miss most bot traffic, which hits static/ISR pages at the edge. You need a **Log Drain** (Pro plan+):

1. Team Settings → Drains → create a drain: type **Logs**, sources: at minimum `static`, `edge`, `lambda`; format **NDJSON**; deliver to an HTTPS endpoint.
2. Endpoint options, cheapest first:
   - **Any webhook-to-storage service** (or a tiny serverless function appending to blob storage) → download files → run `drain_parser.py` on them directly.
   - **PostHog** (if already in the stack): point the drain at a capture endpoint via a small transform, then query with HogQL — pattern documented publicly as "Vercel Log Drains → PostHog". Useful HogQL starting point:

```sql
SELECT
  properties.userAgent AS ua,
  properties.statusCode AS status,
  count() AS hits
FROM events
WHERE event = 'vercel_log'
  AND (ua ILIKE '%GPTBot%' OR ua ILIKE '%OAI-SearchBot%' OR ua ILIKE '%ClaudeBot%'
    OR ua ILIKE '%Claude-SearchBot%' OR ua ILIKE '%Claude-User%' OR ua ILIKE '%ChatGPT-User%'
    OR ua ILIKE '%PerplexityBot%' OR ua ILIKE '%Perplexity-User%' OR ua ILIKE '%bingbot%'
    OR ua ILIKE '%Googlebot%' OR ua ILIKE '%CCBot%' OR ua ILIKE '%Amazonbot%'
    OR ua ILIKE '%Bytespider%' OR ua ILIKE '%meta-externalagent%')
GROUP BY ua, status
ORDER BY hits DESC
```

3. The drain payload's `proxy` object carries what we need: `userAgent`, `statusCode`, `clientIp`, `path`, `timestamp`. `drain_parser.py` reads this schema natively.

## Route 2 — nginx / Apache / anything with access logs

`drain_parser.py --format combined` parses standard combined-format logs directly. This is where **499** appears in nginx: it means the client closed the request before the server finished. Correlate it with user agent, path, request duration, and upstream traces before assigning a cause. Vercel does not use nginx's 499 status in the same way; inspect status, duration, cache status, and function/edge traces together.

## Impostor filtering

Anyone can send `User-Agent: GPTBot`. Before drawing conclusions from log volume, run with `--verify`: it checks vendor-published JSON ranges where available and pinned CIDRs from the registry for Anthropic. It then splits hits into verified vs. unverified. Two reasons to care:
- Impostor volume inflates "AI is crawling us" optimism.
- If a WAF is auto-blocking fake GPTBots by IP reputation, verify the *real* ones (correct IP ranges) are getting 200s — that's the exact failure mode probing can't see.

## Cadence

One-off audits decay. A durable setup is: drain always-on → weekly `drain_parser.py` run → investigate (a) any 4xx/5xx/499 rate > 5% for a retrieval bot, (b) a bot that used to crawl going silent for 14+ days, and (c) the first appearance of a new retrieval bot worth explicit robots.txt treatment. These are monitoring heuristics, not vendor guarantees.
