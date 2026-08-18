#!/usr/bin/env python3
"""
index_stats.py — Aggregate statistics pipeline for the ReadableByAI Index.

Consumes one or more geo_probe.py output files (geo_audit.json shape:
{"generated_at": ..., "results": [...]}) and produces publication-grade
aggregate statistics, split by population (via an optional domain->population
label CSV) and overall.

Every number in stats.md is also in stats.json, so any published claim can be
traced back to a machine-readable source. Exclusions are counted, never
silent: unreachable domains and non-200-baseline domains are pulled out of
every percentage denominator and reported as their own counts.

HONESTY CONTRACT (read before touching the bot-probe sections):
Our probes originate from ONE datacenter IP with a SPOOFED user-agent, not
from the AI crawler's real, verified IP range. A CDN/WAF that does verified-
bot allowlisting by IP will happily challenge our fake "GPTBot" while still
letting the real GPTBot straight through — in either direction, a probe
result here is NOT proof of what the real bot experiences. Empirically (YC
run, 2026-08-08): 123 of 124 AI-bot non-200 responses carried a CDN
challenge-mitigation header; only 1 was a bare 403 with no challenge marker
at all. Treating all of those as "the bot is blocked" would overstate real
blocking by roughly two orders of magnitude. So:
  - Raw-HTML readability (SSR_FULL/SSR_THIN/CSR_SHELL/EMPTY, visible-word
    counts) and robots.txt's literal directives are CONFIRMED observations —
    they don't depend on our probe being mistaken for the real bot.
  - Everything derived from bot-UA probing (differentials, challenges,
    "hard blocks", the robots-vs-edge contradiction metrics) is a LEAD
    requiring server-log confirmation, never a finding, never "blocked."

Zero third-party dependencies: argparse/json/csv/statistics/stdlib only,
matching geo_probe.py's style.

Usage:
  python3 index_stats.py results1.json [results2.json ...] \
      --label-file labels.csv --out ./stats
  python3 index_stats.py --selftest

labels.csv format (header optional): domain,population
  salesforce.com,saas-top50
Domains not present in the label file are bucketed into population
"unlabeled".
"""

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

# ------------------------------------------------------------ small helpers


def pct(n, d):
    """n/d as a percentage rounded to 1 decimal, or None if d == 0."""
    if not d:
        return None
    return round(100.0 * n / d, 1)


def percentile(sorted_vals, p):
    """Linear-interpolation percentile (numpy 'linear' method) over a
    pre-sorted list. Returns None for an empty list."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return round(sorted_vals[int(k)], 3)
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return round(d0 + d1, 3)


def normalize_domain(raw):
    """Extract a bare, lowercase, www-stripped hostname from a domain or URL
    string, for matching against the label file and for population grouping."""
    raw = (raw or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        netloc = urlparse(raw).netloc
    else:
        netloc = raw.split("/")[0]
    netloc = netloc.lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


# -- honest bot-probe classification (FIX 1) --------------------------------
#
# A single, unified classifier used everywhere a probe result needs judging.
# Priority matters and is deliberate:
#   1. probe_error   — transport failure (timeout/reset), not a status at all
#   2. rate_limit    — status 429, its OWN bucket regardless of any challenge
#                       marker also present (rate limiting is a distinct
#                       phenomenon from bot-management challenge/block)
#   3. challenge     — probe's `challenge` array is non-empty, at ANY status.
#                       This is CDN/WAF bot-management mitigation (Cloudflare
#                       interstitial, Vercel mitigation, etc.) — a real
#                       verified bot may sail through this via IP allowlisting
#                       even though our spoofed UA from a datacenter IP did
#                       not. Never call this a "block."
#   4. hard_block    — status in {403, 401, 451} with an EMPTY challenge
#                       array. No CDN mitigation marker fired; this is the
#                       closest thing to a real access-denial candidate, and
#                       even this is still just a lead, not a confirmed block.
#   5. other_non_200 — any other non-200 status (500/502/503/404/etc. without
#                       a challenge marker). Kept as its own bucket instead of
#                       silently folding into hard_block, so nothing is
#                       miscounted as a bot-blocking signal it isn't.
#   6. body_size_anomaly — status 200, no challenge marker, but body is
#                       suspiciously small vs. baseline (heuristic carried
#                       over from the original body-size differential check).
#   7. None          — probe looks like a clean match to baseline; no signal.

HARD_BLOCK_STATUSES = {403, 401, 451}
THIN_CLASSES = {"CSR_SHELL", "SSR_THIN", "EMPTY"}
DIFFERENTIAL_KINDS = ("hard_block", "challenge", "rate_limit", "other_non_200", "body_size_anomaly")

# hard_block still is NOT a confirmed block. Enterprise WAFs (Akamai, AWS
# WAF/CloudFront, Imperva, etc.) commonly return a bare 403 — no challenge
# banner at all — to ANY datacenter IP claiming to be a bot, while
# allowlisting the vendor's real, verified bot by IP. So the absence of a
# challenge marker does not rule out the same verified-bot-inversion pattern
# that the `challenge` bucket exists to flag — it's still just possibly that,
# minus the interstitial page. hard_block is a higher-priority per-domain
# LEAD, never a citable aggregate finding.
HARD_BLOCK_CAVEAT = (
    "Hard blocks from our single datacenter IP with spoofed UAs are higher-priority LEADS "
    "for per-domain verification, not confirmed blocks — enterprise WAFs return bare 403s to "
    "unverified impostors while allowlisting verified bots by IP. Confirm each with the site's "
    "own logs or a verified-IP fetch before naming."
)


def classify_probe(p, baseline_size):
    if p.get("probe_error"):
        return "probe_error"
    status = p.get("status")
    challenge = p.get("challenge") or []
    if status == 429:
        return "rate_limit"
    if challenge:
        return "challenge"
    if status in HARD_BLOCK_STATUSES:
        return "hard_block"
    if status and status != 200:
        return "other_non_200"
    if status == 200:
        size = p.get("size")
        if baseline_size and size is not None and size < baseline_size * 0.25:
            return "body_size_anomaly"
    return None


def prerender_guard(entry):
    """FIX 3 guard: for a CSR_SHELL/SSR_THIN/EMPTY domain, compare GPTBot's
    probe body size to the baseline body size. If GPTBot's body is >2x the
    baseline, the site may be serving bots a materially different (bigger)
    page than it served our browser baseline — meaning our "thin/empty"
    readability read may not reflect what an AI crawler actually receives.
    Flag it POSSIBLE_BOT_PRERENDER and keep it out of the clean, citable
    readability candidate list (still reported, just separated out, never
    silently dropped). Returns (flagged: bool, detail: str|None)."""
    content = entry.get("content") or {}
    cls = content.get("classification")
    if cls not in THIN_CLASSES:
        return False, None
    baseline_size = (entry.get("baseline") or {}).get("size")
    gptbot = (entry.get("probes") or {}).get("GPTBot")
    if not baseline_size or not gptbot:
        return False, None
    size = gptbot.get("size")
    if size is None:
        return False, None
    if size > 2 * baseline_size:
        ratio = round(size / baseline_size, 2)
        detail = (
            f"GPTBot body {size}B vs baseline {baseline_size}B ({ratio}x) — possible "
            f"bot-specific prerendering; excluded from clean readability candidates"
        )
        return True, detail
    return False, None


def classify_unreachable_error(err):
    """Sub-classify a top-level 'error' string (transport-level failure,
    no baseline obtained at all) into a coarse bucket for the error-class
    breakdown."""
    e = (err or "").lower()
    if "timeout" in e:
        return "timeout"
    if "resolve" in e or "dns" in e or "could not resolve" in e:
        return "dns"
    if "ssl" in e or "certificate" in e or "tls" in e:
        return "ssl_tls"
    if "refused" in e or "reset" in e or "connect" in e:
        return "connection"
    return "other"


# --------------------------------------------------------------- load layer


def load_results_files(paths):
    """Load geo_audit.json-shaped files. Accepts either
    {"generated_at": ..., "results": [...]} or a bare list of results.
    Returns (entries, source_meta) where entries is a flat list of
    (source_file, result_dict) and source_meta describes each input file."""
    entries = []
    source_meta = []
    for path in paths:
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, list):
            results = data
            generated_at = None
        elif isinstance(data, dict):
            results = data.get("results", [])
            generated_at = data.get("generated_at")
        else:
            raise ValueError(f"{path}: unrecognized JSON shape (expected object or list)")
        source_meta.append({"file": path, "generated_at": generated_at, "count": len(results)})
        for r in results:
            entries.append((path, r))
    return entries, source_meta


def dedupe(entries):
    """De-duplicate by exact (trimmed, trailing-slash-stripped) domain string.
    Later files win (assume argv order == recency). Returns (deduped_results,
    dropped_list) where dropped_list records what got superseded, so the
    dedup is auditable rather than silent."""
    by_key = {}
    order = []
    dropped = []
    for src, r in entries:
        raw = r.get("domain", "")
        key = raw.strip().rstrip("/")
        if key in by_key:
            prev_src, _ = by_key[key]
            dropped.append({"domain": raw, "kept_from": src, "dropped_from": prev_src})
        else:
            order.append(key)
        by_key[key] = (src, r)
    deduped = [by_key[k][1] for k in order]
    return deduped, dropped


def load_label_file(path):
    """Load a domain,population CSV into {normalized_domain: population}.
    Header row is optional; if the first row's first cell (lowercased) is
    'domain' it's treated as a header and skipped."""
    mapping = {}
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return mapping
    start = 0
    if rows[0] and rows[0][0].strip().lower() == "domain":
        start = 1
    for row in rows[start:]:
        if len(row) < 2 or not row[0].strip():
            continue
        domain, population = row[0].strip(), row[1].strip()
        mapping[normalize_domain(domain)] = population
    return mapping


def assign_populations(deduped_results, label_map):
    """Group results by population label (default 'unlabeled')."""
    groups = defaultdict(list)
    for r in deduped_results:
        norm = normalize_domain(r.get("domain", ""))
        population = label_map.get(norm, "unlabeled")
        groups[population].append(r)
    return groups


# ---------------------------------------------------------- aggregate layer


def compute_stats(population_name, entries):
    """Compute the full stats block for one population (or 'overall')."""
    size = len(entries)
    errored = [e for e in entries if "error" in e]
    reachable = [e for e in entries if "error" not in e]
    non200 = [e for e in reachable if (e.get("baseline") or {}).get("status") != 200]
    clean = [e for e in reachable if (e.get("baseline") or {}).get("status") == 200]
    n_clean = len(clean)

    unreachable_breakdown = dict(Counter(classify_unreachable_error(e.get("error")) for e in errored))
    non200_breakdown = dict(Counter(str((e.get("baseline") or {}).get("status")) for e in non200))

    # -- FIX 3 headline: raw-HTML readability (confirmed observation) -------
    content_counter = Counter((e.get("content") or {}).get("classification", "UNKNOWN") for e in clean)
    content_dist = {}
    for cls in ["SSR_FULL", "SSR_THIN", "CSR_SHELL", "EMPTY"]:
        content_dist[cls] = {"count": content_counter.get(cls, 0), "pct": pct(content_counter.get(cls, 0), n_clean)}
    for cls, cnt in content_counter.items():
        if cls not in content_dist:
            content_dist[cls] = {"count": cnt, "pct": pct(cnt, n_clean)}
    word_counts = sorted(
        (e.get("content") or {}).get("visible_words")
        for e in clean
        if (e.get("content") or {}).get("visible_words") is not None
    )
    median_words = percentile(word_counts, 50) if word_counts else None

    # -- robots.txt presence + per-bot breakdown (literal file contents —
    #    confirmed observation, not a probe result) -------------------------
    robots_present = sum(1 for e in clean if (e.get("robots") or {}).get("status") == 200)
    robots_tokens = set()
    for e in clean:
        robots_tokens.update((e.get("robots") or {}).get("bots", {}).keys())
    per_bot_robots = {}
    for token in sorted(robots_tokens):
        denom = 0
        buckets = Counter()
        for e in clean:
            b = (e.get("robots") or {}).get("bots", {}).get(token)
            if b is None:
                continue
            denom += 1
            allowed, explicit = b.get("allowed"), b.get("explicit")
            if explicit and allowed:
                buckets["explicit_allowed"] += 1
            elif explicit and not allowed:
                buckets["explicit_blocked"] += 1
            elif not explicit and allowed:
                buckets["default_allowed"] += 1
            else:
                buckets["default_blocked"] += 1
        per_bot_robots[token] = {
            "denominator": denom,
            "explicit_blocked": {"count": buckets["explicit_blocked"], "pct": pct(buckets["explicit_blocked"], denom)},
            "explicit_allowed": {"count": buckets["explicit_allowed"], "pct": pct(buckets["explicit_allowed"], denom)},
            "default_allowed": {"count": buckets["default_allowed"], "pct": pct(buckets["default_allowed"], denom)},
            "default_blocked": {"count": buckets["default_blocked"], "pct": pct(buckets["default_blocked"], denom)},
        }

    # -- FIX 1 + FIX 2: honest per-bot probe classification ------------------
    probe_tokens = set()
    for e in clean:
        probe_tokens.update((e.get("probes") or {}).keys())

    domains_with_signal = 0
    kind_counts = Counter()
    per_bot_kind = {t: Counter() for t in probe_tokens}
    raw_status_per_bot = {t: Counter() for t in probe_tokens}

    hard403_per_bot = Counter()
    hard403_domains = []
    challenged_per_bot = Counter()
    challenged_domains = []

    for e in clean:
        probes = e.get("probes") or {}
        robots_bots = (e.get("robots") or {}).get("bots", {})
        baseline_size = (e.get("baseline") or {}).get("size")
        has_signal_this_domain = False
        for token, p in probes.items():
            kind = classify_probe(p, baseline_size)
            if p.get("status"):
                raw_status_per_bot[token][str(p["status"])] += 1
            elif kind == "probe_error":
                raw_status_per_bot[token]["probe_error"] += 1
            if kind and kind != "probe_error":
                kind_counts[kind] += 1
                per_bot_kind[token][kind] += 1
                has_signal_this_domain = True

            rb = robots_bots.get(token)
            robots_allows = bool(rb and rb.get("allowed"))
            if robots_allows and kind == "hard_block":
                hard403_per_bot[token] += 1
                hard403_domains.append({"domain": e.get("domain"), "bot": token, "status": p.get("status")})
            elif robots_allows and kind == "challenge":
                challenged_per_bot[token] += 1
                challenged_domains.append(
                    {"domain": e.get("domain"), "bot": token, "status": p.get("status"), "challenge": p.get("challenge")}
                )
        if has_signal_this_domain:
            domains_with_signal += 1

    per_bot_classification = {
        token: {kind: per_bot_kind[token].get(kind, 0) for kind in DIFFERENTIAL_KINDS}
        for token in sorted(probe_tokens)
    }
    raw_status_out = {token: dict(raw_status_per_bot[token]) for token in sorted(probe_tokens)}

    # -- score distribution (item 6) -----------------------------------------
    scores = sorted(e.get("score") for e in clean if e.get("score") is not None)
    score_block = None
    if scores:
        hist = {"0-49": 0, "50-69": 0, "70-89": 0, "90-100": 0}
        for s in scores:
            if s <= 49:
                hist["0-49"] += 1
            elif s <= 69:
                hist["50-69"] += 1
            elif s <= 89:
                hist["70-89"] += 1
            else:
                hist["90-100"] += 1
        score_block = {
            "n": len(scores),
            "median": percentile(scores, 50),
            "p25": percentile(scores, 25),
            "p75": percentile(scores, 75),
            "histogram": hist,
        }

    # -- TTFB (item 7) --------------------------------------------------------
    ttfb_vals = sorted(e.get("bot_ttfb_median") for e in clean if e.get("bot_ttfb_median") is not None)
    ttfb_block = None
    if ttfb_vals:
        over = sum(1 for v in ttfb_vals if v > 1.2)
        ttfb_block = {
            "n": len(ttfb_vals),
            "median_bot_ttfb_median": percentile(ttfb_vals, 50),
            "pct_over_1_2s": pct(over, len(ttfb_vals)),
            "count_over_1_2s": over,
        }

    # -- llms.txt (item 8) ------------------------------------------------------
    llms_count = sum(1 for e in clean if e.get("llms_txt") is True)

    # -- FIX 3: named candidates with the bot-prerender guard -----------------
    flagged = {}
    for e in clean:
        flag, detail = prerender_guard(e)
        if flag:
            flagged[e.get("domain")] = detail

    ranked = sorted(clean, key=lambda e: (e.get("score") is None, e.get("score")))
    worst_survivors, worst_excluded = [], []
    for e in ranked:
        dom = e.get("domain")
        row = {
            "domain": dom,
            "score": e.get("score"),
            "classification": (e.get("content") or {}).get("classification"),
        }
        if dom in flagged:
            row["reason"] = flagged[dom]
            worst_excluded.append(row)
        elif len(worst_survivors) < 10:
            worst_survivors.append(row)

    return {
        "population": population_name,
        "size": size,
        "probed_ok": n_clean,
        "non_200_baseline": {
            "count": len(non200),
            "breakdown_by_status": non200_breakdown,
        },
        "errored_unreachable": {
            "count": len(errored),
            "breakdown_by_class": unreachable_breakdown,
        },
        "excluded_total": len(non200) + len(errored),
        "readability": {
            "note": "CONFIRMED observation — raw HTML as served to our baseline browser fetch, "
                    "independent of bot-UA spoofing concerns.",
            "classification": content_dist,
            "median_visible_words": median_words,
        },
        "robots": {
            "note": "CONFIRMED observation — literal robots.txt directives, not a probe result.",
            "present_count": robots_present,
            "present_pct": pct(robots_present, n_clean),
            "denominator": n_clean,
            "per_bot": per_bot_robots,
        },
        "probe_classification": {
            "note": "LEADS REQUIRING LOG CONFIRMATION, not findings. Probes run from one datacenter "
                    "IP with a spoofed user-agent. 'challenge' means a CDN/WAF bot-management marker "
                    "fired (e.g. Cloudflare/Vercel mitigation) — a real, verified bot may still pass "
                    "via IP allowlisting even though our probe didn't. 'hard_block' means a 403/401/451 "
                    "with NO challenge marker at all — the closest thing to a real access-denial "
                    "candidate, and still unconfirmed without server logs.",
            "denominator": n_clean,
            "domains_with_any_signal": {"count": domains_with_signal, "pct": pct(domains_with_signal, n_clean)},
            "by_kind": {k: kind_counts.get(k, 0) for k in DIFFERENTIAL_KINDS},
            "per_bot": per_bot_classification,
            "raw_status_per_bot": raw_status_out,
        },
        "robots_vs_edge": {
            "robots_allows_but_hard_403": {
                "note": "Bot is allowed (explicit or default) in robots.txt AND the probe hit a "
                        "403/401/451 with NO CDN challenge marker. A higher-priority per-domain lead — "
                        "nothing probe-derived is citable as an aggregate; only readability and "
                        "literal robots.txt contents are. " + HARD_BLOCK_CAVEAT,
                "total_count": sum(hard403_per_bot.values()),
                "per_bot": dict(hard403_per_bot),
                "domains": hard403_domains,
            },
            "robots_allows_but_challenged": {
                "note": "Bot is allowed in robots.txt AND the probe was CDN-challenged. Edge "
                        "challenges unverified fetchers; whether the site allowlists verified AI "
                        "bots by IP cannot be determined from active probing — server logs required. "
                        "Do NOT sum this with robots_allows_but_hard_403 — they are different claims.",
                "total_count": sum(challenged_per_bot.values()),
                "per_bot": dict(challenged_per_bot),
                "domains": challenged_domains,
            },
        },
        "score": score_block,
        "ttfb": ttfb_block,
        "llms_txt": {"present_count": llms_count, "present_pct": pct(llms_count, n_clean), "denominator": n_clean},
        "named_candidates": {
            "note": "UNVERIFIED CANDIDATES — hand-verification targets, not findings.",
            "worst_by_score": worst_survivors,
            "excluded_possible_bot_prerender": worst_excluded,
        },
    }


# ----------------------------------------------------------------- markdown


def render_markdown(overall, populations, meta):
    lines = [
        "# ReadableByAI Index — Aggregate Statistics",
        f"\n**Generated:** {meta['generated_at']}  ",
        f"**Source files:** {', '.join(m['file'] for m in meta['source_files'])}  ",
        f"**Raw result rows read:** {meta['raw_row_count']} · **After dedup:** {meta['deduped_count']}"
        + (f" ({len(meta['dropped'])} duplicate domain(s) dropped, later file wins)" if meta["dropped"] else ""),
    ]
    if meta.get("label_file"):
        lines.append(f"**Label file:** {meta['label_file']}")
    lines.append(
        "\n> Non-200-baseline (anomalous) and unreachable domains are excluded from every "
        "percentage denominator below and reported as their own counts — never silently.\n"
        "\n> **Honesty contract:** raw-HTML readability and literal robots.txt contents are "
        "CONFIRMED observations. Everything below derived from bot-UA probing (challenges, "
        "hard-blocks, rate-limits, the robots-vs-edge metrics) is a **lead requiring server-log "
        "confirmation** — our probes run from one datacenter IP with a spoofed user-agent, so a "
        "CDN challenge here does not mean the real, IP-verified bot is blocked."
    )

    def section(stats):
        out = []
        out.append(f"\n## {stats['population']}\n")
        out.append(
            f"- Population size: **{stats['size']}**  ·  probed OK (clean 200 baseline): "
            f"**{stats['probed_ok']}**  ·  non-200 baseline (excluded): "
            f"**{stats['non_200_baseline']['count']}**  ·  unreachable/errored (excluded): "
            f"**{stats['errored_unreachable']['count']}**"
        )
        if stats["non_200_baseline"]["breakdown_by_status"]:
            out.append(f"  - non-200 baseline breakdown: {stats['non_200_baseline']['breakdown_by_status']}")
        if stats["errored_unreachable"]["breakdown_by_class"]:
            out.append(f"  - unreachable error-class breakdown: {stats['errored_unreachable']['breakdown_by_class']}")

        n = stats["probed_ok"]
        out.append(f"\nAll stats below are over the **{n}** clean-baseline (200) domains unless noted.\n")

        # ---- HEADLINE: raw-HTML readability (FIX 3) ----
        out.append("### Raw-HTML readability — CONFIRMED, the headline metric\n")
        rd = stats["readability"]
        out.append(f"_{rd['note']}_\n")
        out.append(f"Median visible words (clean-baseline): **{rd['median_visible_words']}**\n")
        out.append("| Class | Count | % of clean-baseline |")
        out.append("|---|---|---|")
        for cls in ["SSR_FULL", "SSR_THIN", "CSR_SHELL", "EMPTY"]:
            c = rd["classification"].get(cls, {"count": 0, "pct": None})
            out.append(f"| {cls} | {c['count']} | {c['pct']}% |" if c["pct"] is not None else f"| {cls} | {c['count']} | — |")

        out.append("\n### robots.txt — CONFIRMED (literal file contents)\n")
        rb = stats["robots"]
        out.append(f"robots.txt present: **{rb['present_count']}/{rb['denominator']}** ({rb['present_pct']}%)\n")
        out.append("| Bot token | n | explicit blocked | explicit allowed | default allowed | default blocked |")
        out.append("|---|---|---|---|---|---|")
        for token, b in rb["per_bot"].items():
            out.append(
                f"| {token} | {b['denominator']} "
                f"| {b['explicit_blocked']['count']} ({b['explicit_blocked']['pct']}%) "
                f"| {b['explicit_allowed']['count']} ({b['explicit_allowed']['pct']}%) "
                f"| {b['default_allowed']['count']} ({b['default_allowed']['pct']}%) "
                f"| {b['default_blocked']['count']} ({b['default_blocked']['pct']}%) |"
            )

        out.append("\n### Bot-probe classification — LEADS REQUIRING LOG CONFIRMATION\n")
        pc = stats["probe_classification"]
        out.append(f"> {pc['note']}\n")
        out.append(
            f"Domains with >=1 probe signal (any kind below): "
            f"**{pc['domains_with_any_signal']['count']}/{pc['denominator']}** "
            f"({pc['domains_with_any_signal']['pct']}%)\n"
        )
        out.append("| Kind | Count | Meaning |")
        out.append("|---|---|---|")
        meanings = {
            "hard_block": "403/401/451, no challenge marker — closest to a real block candidate",
            "challenge": "CDN/WAF challenge marker fired — real verified bot may still pass",
            "rate_limit": "429 — rate limiting, not an access decision",
            "other_non_200": "other non-200 status, no challenge marker (5xx/404/etc.)",
            "body_size_anomaly": "200 OK but body <25% of baseline size",
        }
        for kind in DIFFERENTIAL_KINDS:
            out.append(f"| {kind} | {pc['by_kind'].get(kind, 0)} | {meanings[kind]} |")
        out.append(f"\n> **hard_block caveat:** {HARD_BLOCK_CAVEAT}\n")

        out.append("\n**Per-bot breakdown (clean-baseline domains):**\n")
        out.append("| Bot token | hard_block | challenge | rate_limit | other_non_200 | body_size_anomaly |")
        out.append("|---|---|---|---|---|---|")
        for token, b in pc["per_bot"].items():
            out.append(
                f"| {token} | {b['hard_block']} | {b['challenge']} | {b['rate_limit']} "
                f"| {b['other_non_200']} | {b['body_size_anomaly']} |"
            )

        out.append("\n### robots-vs-edge — two separate metrics, never summed\n")
        rve = stats["robots_vs_edge"]
        h = rve["robots_allows_but_hard_403"]
        out.append(f"**robots_allows_but_hard_403** — {h['note']}\n")
        out.append(f"Total: **{h['total_count']}**\n")
        if h["per_bot"]:
            out.append("| Bot token | Count |")
            out.append("|---|---|")
            for token, c in sorted(h["per_bot"].items(), key=lambda x: -x[1]):
                out.append(f"| {token} | {c} |")
        ch = rve["robots_allows_but_challenged"]
        out.append(f"\n**robots_allows_but_challenged** — {ch['note']}\n")
        out.append(f"Total: **{ch['total_count']}**\n")
        if ch["per_bot"]:
            out.append("| Bot token | Count |")
            out.append("|---|---|")
            for token, c in sorted(ch["per_bot"].items(), key=lambda x: -x[1]):
                out.append(f"| {token} | {c} |")

        out.append("\n### Score distribution\n")
        if stats["score"]:
            s = stats["score"]
            out.append(f"n={s['n']} · median **{s['median']}** · p25 {s['p25']} · p75 {s['p75']}\n")
            out.append("| Bucket | Count |")
            out.append("|---|---|")
            for b in ["0-49", "50-69", "70-89", "90-100"]:
                out.append(f"| {b} | {s['histogram'][b]} |")
        else:
            out.append("_no clean-baseline domains with a score_")

        out.append("\n### TTFB\n")
        if stats["ttfb"]:
            t = stats["ttfb"]
            out.append(
                f"median of bot_ttfb_median across domains: **{t['median_bot_ttfb_median']}s** "
                f"(n={t['n']}) · domains with bot ttfb median > 1.2s: "
                f"**{t['count_over_1_2s']}/{t['n']}** ({t['pct_over_1_2s']}%)"
            )
        else:
            out.append("_no clean-baseline domains with bot TTFB data_")

        out.append("\n### llms.txt (footnote-grade)\n")
        lt = stats["llms_txt"]
        out.append(f"present: **{lt['present_count']}/{lt['denominator']}** ({lt['present_pct']}%)")

        out.append("\n### Named candidates — UNVERIFIED CANDIDATES, not findings\n")
        out.append("These are hand-verification targets only. Do not cite as confirmed results.\n")
        out.append("**Worst by score (bot-prerender-guard survivors, up to 10):**\n")
        nc = stats["named_candidates"]
        if nc["worst_by_score"]:
            out.append("| Domain | Score | Classification |")
            out.append("|---|---|---|")
            for w in nc["worst_by_score"]:
                out.append(f"| {w['domain']} | {w['score']} | {w['classification']} |")
        else:
            out.append("_none_")
        out.append(
            "\n**Excluded — POSSIBLE_BOT_PRERENDER** (GPTBot's body was >2x baseline size; the site "
            "may serve bots a materially different page than our browser baseline, so these are held "
            "out of the clean readability candidates rather than silently included):\n"
        )
        if nc["excluded_possible_bot_prerender"]:
            out.append("| Domain | Score | Classification | Detail |")
            out.append("|---|---|---|---|")
            for w in nc["excluded_possible_bot_prerender"]:
                out.append(f"| {w['domain']} | {w['score']} | {w['classification']} | {w['reason']} |")
        else:
            out.append("_none_")

        return "\n".join(out)

    lines.append(section(overall))
    for name in sorted(populations.keys()):
        if populations[name]["size"] == 0:
            continue
        lines.append(section(populations[name]))

    return "\n".join(lines)


# ------------------------------------------------------------------ selftest


def build_selftest_data():
    """8 synthetic result dicts exercising every stat path, including the
    FIX 1/2/3 correctness fixes:
      - healthy.com          clean, no signal anywhere
      - hardblock.com        GPTBot 403 with EMPTY challenge array -> hard_block,
                              robots allows GPTBot -> robots_allows_but_hard_403
      - challenged.com       GPTBot 403 WITH a challenge marker -> challenge
                              (decoy: robots also allows GPTBot here, but this
                              must land in robots_allows_but_challenged, NOT
                              robots_allows_but_hard_403)
      - ratelimited.com      Amazonbot 429 WITH a challenge marker present ->
                              must classify as rate_limit (priority over
                              challenge), and must NOT feed either robots-vs-
                              edge metric
      - prerender.com        CSR_SHELL, GPTBot 200 with body >2x baseline ->
                              POSSIBLE_BOT_PRERENDER, excluded from the clean
                              worst-by-score list despite the lowest score
      - anomalous.com        non-200 baseline, excluded from everything
      - unreachable.com      top-level error, excluded from everything
      - empty.com            EMPTY classification, no robots.txt, GPTBot body
                              ~= baseline size -> NOT prerender-flagged, stays
                              in the clean worst-by-score list
    """
    return [
        {
            "domain": "healthy.com",
            "baseline": {"status": 200, "warm_ttfb": 0.2, "size": 20000},
            "content": {"classification": "SSR_FULL", "visible_words": 1200},
            "robots": {
                "status": 200,
                "bots": {
                    "GPTBot": {"allowed": True, "explicit": True},
                    "ClaudeBot": {"allowed": False, "explicit": True},
                },
            },
            "llms_txt": True,
            "probes": {
                "GPTBot": {"status": 200, "size": 19800, "challenge": []},
                "ClaudeBot": {"status": 200, "size": 19900, "challenge": []},
            },
            "bot_ttfb_median": 0.3,
            "score": 95,
        },
        {
            "domain": "hardblock.com",
            "baseline": {"status": 200, "warm_ttfb": 0.4, "size": 8000},
            "content": {"classification": "SSR_THIN", "visible_words": 200},
            "robots": {
                "status": 200,
                "bots": {
                    "GPTBot": {"allowed": True, "explicit": True},
                    "ClaudeBot": {"allowed": True, "explicit": False},
                },
            },
            "llms_txt": False,
            "probes": {
                "GPTBot": {"status": 403, "size": 1200, "challenge": []},
                "ClaudeBot": {"status": 200, "size": 7900, "challenge": []},
            },
            "bot_ttfb_median": 0.4,
            "score": 55,
        },
        {
            "domain": "challenged.com",
            "baseline": {"status": 200, "warm_ttfb": 0.5, "size": 5000},
            "content": {"classification": "CSR_SHELL", "visible_words": 50},
            "robots": {
                "status": 200,
                "bots": {
                    "GPTBot": {"allowed": True, "explicit": True},
                    "PerplexityBot": {"allowed": True, "explicit": False},
                },
            },
            "llms_txt": False,
            "probes": {
                "GPTBot": {"status": 403, "size": 1400, "challenge": ["cloudflare-403"]},
                "PerplexityBot": {"status": 200, "size": 4900, "challenge": []},
            },
            "bot_ttfb_median": 0.5,
            "score": 45,
        },
        {
            "domain": "ratelimited.com",
            "baseline": {"status": 200, "warm_ttfb": 0.35, "size": 15000},
            "content": {"classification": "SSR_FULL", "visible_words": 600},
            "robots": {
                "status": 200,
                "bots": {"Amazonbot": {"allowed": True, "explicit": False}},
            },
            "llms_txt": False,
            "probes": {
                "Amazonbot": {"status": 429, "size": 100, "challenge": ["vercel-429"]},
            },
            "bot_ttfb_median": 0.35,
            "score": 65,
        },
        {
            "domain": "prerender.com",
            "baseline": {"status": 200, "warm_ttfb": 0.4, "size": 8000},
            "content": {"classification": "CSR_SHELL", "visible_words": 30},
            "robots": {"status": 200, "bots": {"GPTBot": {"allowed": True, "explicit": False}}},
            "llms_txt": False,
            "probes": {
                "GPTBot": {"status": 200, "size": 40000, "challenge": []},
            },
            "bot_ttfb_median": 1.5,
            "score": 30,
        },
        {
            "domain": "anomalous.com",
            "baseline": {"status": 404, "warm_ttfb": 0.2, "size": 500},
            "content": {"classification": "EMPTY", "visible_words": 0},
            "robots": {"status": 200, "bots": {"GPTBot": {"allowed": True, "explicit": False}}},
            "llms_txt": False,
            "probes": {"GPTBot": {"status": 404, "size": 500, "challenge": []}},
            "bot_ttfb_median": 0.2,
            "score": 50,
        },
        {
            "domain": "unreachable.com",
            "error": "hard timeout",
        },
        {
            "domain": "empty.com",
            "baseline": {"status": 200, "warm_ttfb": 0.9, "size": 200},
            "content": {"classification": "EMPTY", "visible_words": 0},
            "robots": {"status": 404, "bots": {"GPTBot": {"allowed": True, "explicit": False}}},
            "llms_txt": False,
            "probes": {"GPTBot": {"status": 200, "size": 190, "challenge": []}},
            "bot_ttfb_median": 0.9,
            "score": 15,
        },
    ]


def run_selftest():
    data = build_selftest_data()
    stats = compute_stats("selftest", data)

    def check(label, actual, expected):
        assert actual == expected, f"FAIL [{label}]: expected {expected!r}, got {actual!r}"

    check("population size", stats["size"], 8)
    check("probed_ok", stats["probed_ok"], 6)
    check("non_200_baseline count", stats["non_200_baseline"]["count"], 1)
    check("non_200_baseline breakdown", stats["non_200_baseline"]["breakdown_by_status"], {"404": 1})
    check("errored count", stats["errored_unreachable"]["count"], 1)
    check("errored breakdown", stats["errored_unreachable"]["breakdown_by_class"], {"timeout": 1})
    check("excluded_total", stats["excluded_total"], 2)

    # -- readability (FIX 3 headline): SSR_FULL 2, SSR_THIN 1, CSR_SHELL 2, EMPTY 1 over 6 clean
    rd = stats["readability"]["classification"]
    check("SSR_FULL count", rd["SSR_FULL"]["count"], 2)
    check("SSR_THIN count", rd["SSR_THIN"]["count"], 1)
    check("CSR_SHELL count", rd["CSR_SHELL"]["count"], 2)
    check("EMPTY count", rd["EMPTY"]["count"], 1)
    check("SSR_FULL pct", rd["SSR_FULL"]["pct"], 33.3)
    # median visible_words of [0,30,50,200,600,1200] -> 125.0
    check("median visible words", stats["readability"]["median_visible_words"], 125.0)

    # robots presence: 5/6 (empty.com has no robots.txt)
    check("robots present_count", stats["robots"]["present_count"], 5)
    check("robots present_pct", stats["robots"]["present_pct"], 83.3)

    # per-bot robots breakdown
    gpt = stats["robots"]["per_bot"]["GPTBot"]
    check("GPTBot robots denom", gpt["denominator"], 5)  # all but ratelimited.com
    check("GPTBot explicit_allowed", gpt["explicit_allowed"]["count"], 3)
    check("GPTBot default_allowed", gpt["default_allowed"]["count"], 2)

    # -- FIX 1: honest classification. Only GPTBot@hardblock.com is hard_block;
    # GPTBot@challenged.com is challenge (has a marker); Amazonbot@ratelimited.com
    # is rate_limit despite carrying a challenge marker (429 takes priority);
    # GPTBot@prerender.com and GPTBot@empty.com are both None (size differs in
    # opposite directions from the body_size_anomaly shrink heuristic).
    pcls = stats["probe_classification"]
    check("by_kind", pcls["by_kind"], {
        "hard_block": 1, "challenge": 1, "rate_limit": 1, "other_non_200": 0, "body_size_anomaly": 0,
    })
    check("domains_with_any_signal", pcls["domains_with_any_signal"]["count"], 3)
    check("domains_with_any_signal pct", pcls["domains_with_any_signal"]["pct"], 50.0)
    check("GPTBot per-bot kinds", pcls["per_bot"]["GPTBot"],
          {"hard_block": 1, "challenge": 1, "rate_limit": 0, "other_non_200": 0, "body_size_anomaly": 0})
    check("Amazonbot per-bot kinds", pcls["per_bot"]["Amazonbot"],
          {"hard_block": 0, "challenge": 0, "rate_limit": 1, "other_non_200": 0, "body_size_anomaly": 0})

    # -- FIX 2: the two contradiction metrics must NOT be conflated.
    rve = stats["robots_vs_edge"]
    check("robots_allows_but_hard_403 total", rve["robots_allows_but_hard_403"]["total_count"], 1)
    check("robots_allows_but_hard_403 per_bot", rve["robots_allows_but_hard_403"]["per_bot"], {"GPTBot": 1})
    check("robots_allows_but_hard_403 domains", [d["domain"] for d in rve["robots_allows_but_hard_403"]["domains"]],
          ["hardblock.com"])
    check("robots_allows_but_challenged total", rve["robots_allows_but_challenged"]["total_count"], 1)
    check("robots_allows_but_challenged per_bot", rve["robots_allows_but_challenged"]["per_bot"], {"GPTBot": 1})
    check("robots_allows_but_challenged domains",
          [d["domain"] for d in rve["robots_allows_but_challenged"]["domains"]], ["challenged.com"])
    # ratelimited.com's Amazonbot (rate_limit, robots-allowed) must appear in NEITHER metric
    all_hard_domains = {d["domain"] for d in rve["robots_allows_but_hard_403"]["domains"]}
    all_challenged_domains = {d["domain"] for d in rve["robots_allows_but_challenged"]["domains"]}
    assert "ratelimited.com" not in all_hard_domains, "FAIL: rate_limit leaked into hard_403 contradiction"
    assert "ratelimited.com" not in all_challenged_domains, "FAIL: rate_limit leaked into challenged contradiction"

    # score distribution: sorted [15, 30, 45, 55, 65, 95]
    check("score n", stats["score"]["n"], 6)
    check("score median", stats["score"]["median"], 50.0)
    check("score p25", stats["score"]["p25"], 33.75)
    check("score p75", stats["score"]["p75"], 62.5)
    check("score histogram", stats["score"]["histogram"],
          {"0-49": 3, "50-69": 2, "70-89": 0, "90-100": 1})

    # ttfb: sorted [0.3, 0.35, 0.4, 0.5, 0.9, 1.5], median 0.45, 1 domain (prerender) > 1.2s
    check("ttfb n", stats["ttfb"]["n"], 6)
    check("ttfb median", stats["ttfb"]["median_bot_ttfb_median"], 0.45)
    check("ttfb count_over_1_2s", stats["ttfb"]["count_over_1_2s"], 1)
    check("ttfb pct_over_1_2s", stats["ttfb"]["pct_over_1_2s"], 16.7)

    # llms.txt: only healthy.com -> 1/6
    check("llms present_count", stats["llms_txt"]["present_count"], 1)
    check("llms present_pct", stats["llms_txt"]["present_pct"], 16.7)

    # -- FIX 3: prerender guard. prerender.com has the lowest score (30) but
    # must be EXCLUDED from worst_by_score and appear in the excluded list
    # instead; empty.com (score 15, also thin/empty) must survive since its
    # GPTBot body is ~= baseline, not >2x.
    nc = stats["named_candidates"]
    survivors = [w["domain"] for w in nc["worst_by_score"]]
    check("worst_by_score order", survivors,
          ["empty.com", "challenged.com", "hardblock.com", "ratelimited.com", "healthy.com"])
    assert "prerender.com" not in survivors, "FAIL: prerender-flagged domain leaked into clean worst-by-score list"
    excluded = [w["domain"] for w in nc["excluded_possible_bot_prerender"]]
    check("excluded_possible_bot_prerender", excluded, ["prerender.com"])

    # dedup + population assignment plumbing, exercised end to end
    entries = [("run1.json", d) for d in data] + [("run2.json", dict(data[0]))]  # duplicate healthy.com
    deduped, dropped = dedupe(entries)
    check("dedup count", len(deduped), 8)
    check("dedup dropped count", len(dropped), 1)
    check("dedup keeps later file", dropped[0]["dropped_from"], "run1.json")

    label_map = {"healthy.com": "pop-a", "hardblock.com": "pop-a"}
    groups = assign_populations(deduped, label_map)
    check("pop-a size", len(groups["pop-a"]), 2)
    check("unlabeled size", len(groups["unlabeled"]), 6)

    print("PASS — all selftest assertions passed "
          "(8 synthetic domains: challenge-vs-hard-block split, rate_limit priority, "
          "bot-prerender guard, dedup + population grouping all verified)")


# ---------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description="Aggregate statistics for the ReadableByAI Index")
    ap.add_argument("results", nargs="*", help="geo_audit.json files (one per probe run)")
    ap.add_argument("--label-file", help="CSV mapping domain,population")
    ap.add_argument("--out", default="./stats", help="output directory for stats.json / stats.md")
    ap.add_argument("--selftest", action="store_true", help="run synthetic self-test and exit")
    args = ap.parse_args()

    if args.selftest:
        run_selftest()
        return

    if not args.results:
        ap.error("no input files given (or use --selftest)")

    entries, source_meta = load_results_files(args.results)
    deduped, dropped = dedupe(entries)

    label_map = {}
    if args.label_file:
        label_map = load_label_file(args.label_file)

    populations = assign_populations(deduped, label_map)
    pop_stats = {name: compute_stats(name, results) for name, results in populations.items()}
    overall_stats = compute_stats("overall", deduped)

    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source_files": source_meta,
        "raw_row_count": len(entries),
        "deduped_count": len(deduped),
        "dropped": dropped,
        "label_file": args.label_file,
    }

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "stats.json")
    md_path = os.path.join(args.out, "stats.md")

    with open(json_path, "w") as fh:
        json.dump({"meta": meta, "overall": overall_stats, "populations": pop_stats}, fh, indent=2)

    with open(md_path, "w") as fh:
        fh.write(render_markdown(overall_stats, pop_stats, meta))

    print(f"Wrote {json_path}\nWrote {md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
