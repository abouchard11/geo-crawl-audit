#!/usr/bin/env python3
"""
drain_parser.py — Ground-truth AI bot traffic analysis from server logs.

The active probe (geo_probe.py) tells you what filtering *exists*; logs tell
you what actually *happened* to real crawlers. This parser answers, per bot:
did it come, how often, what status did it get, did it abandon (499), what
did it read, and was it really that bot (published-IP verification) or an
impostor.

Accepts:
  - Vercel Log Drain exports: NDJSON / JSON array (proxy.* schema)
  - Generic nginx/apache combined-format access logs

Usage:
  python3 drain_parser.py logs/*.ndjson --out ./audit-results
  python3 drain_parser.py access.log --format combined --verify
"""

import argparse
import glob
import ipaddress
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

COMBINED_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+)[^"]*" '
    r'(?P<status>\d{3}) (?P<size>\S+)(?: "(?P<referer>[^"]*)" "(?P<ua>[^"]*)")?'
)

VERIFY_SOURCES = {
    "GPTBot": "https://openai.com/gptbot.json",
    "OAI-SearchBot": "https://openai.com/searchbot.json",
    "ChatGPT-User": "https://openai.com/chatgpt-user.json",
    "PerplexityBot": "https://www.perplexity.ai/perplexitybot.json",
    "Perplexity-User": "https://www.perplexity.ai/perplexity-user.json",
    "bingbot": "https://www.bing.com/toolbox/bingbot.json",
    "Googlebot": "https://developers.google.com/static/search/apis/ipranges/googlebot.json",
}


def load_registry(path):
    with open(path) as fh:
        reg = json.load(fh)
    tokens = {}
    for b in reg["bots"]:
        if not b.get("robots_token_only"):
            tokens[b["token"].lower()] = {"token": b["token"], "category": b["category"]}
    # Bots worth tracking in logs even though we don't probe them
    tokens.setdefault("googlebot", {"token": "Googlebot", "category": "retrieval"})
    tokens.setdefault("applebot", {"token": "Applebot", "category": "retrieval"})
    return tokens


def iter_records(paths, fmt):
    """Yield normalized {ip, ua, status, path, time} dicts from log files."""
    for path in paths:
        with open(path, errors="replace") as fh:
            first = fh.read(1)
            fh.seek(0)
            if fmt == "combined" or (fmt == "auto" and first not in "[{"):
                for line in fh:
                    m = COMBINED_RE.match(line)
                    if m:
                        yield {"ip": m["ip"], "ua": m["ua"] or "", "status": int(m["status"]),
                               "path": m["path"], "time": m["time"]}
                continue
            if first == "[":  # JSON array
                try:
                    entries = json.load(fh)
                except json.JSONDecodeError:
                    continue
            else:  # NDJSON
                entries = (json.loads(ln) for ln in fh if ln.strip())
            for e in entries:
                if not isinstance(e, dict):
                    continue
                proxy = e.get("proxy") or {}
                ua = proxy.get("userAgent") or e.get("userAgent") or e.get("user_agent") or ""
                if isinstance(ua, list):
                    ua = ua[0] if ua else ""
                status = proxy.get("statusCode") or e.get("statusCode") or e.get("status") or 0
                yield {
                    "ip": proxy.get("clientIp") or e.get("clientIp") or e.get("ip") or "",
                    "ua": ua,
                    "status": int(status) if status else 0,
                    "path": proxy.get("path") or e.get("path") or "",
                    "time": proxy.get("timestamp") or e.get("timestamp") or "",
                    "duration": e.get("durationMs") or e.get("duration"),
                }


def fetch_ranges(url):
    """Fetch a published bot IP-range JSON; returns list of ip_network."""
    try:
        raw = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "15", url],
            capture_output=True, text=True, timeout=25,
        ).stdout
        data = json.loads(raw)
    except Exception:
        return None
    nets = []
    for p in data.get("prefixes", []):
        cidr = p.get("ipv4Prefix") or p.get("ipv6Prefix")
        if cidr:
            try:
                nets.append(ipaddress.ip_network(cidr))
            except ValueError:
                pass
    return nets or None


def main():
    ap = argparse.ArgumentParser(description="AI bot log analysis")
    ap.add_argument("logs", nargs="+", help="log files (globs ok)")
    ap.add_argument("--format", choices=["auto", "combined", "json"], default="auto")
    ap.add_argument("--bots", default=os.path.join(HERE, "bots.json"))
    ap.add_argument("--out", default=".")
    ap.add_argument("--verify", action="store_true",
                    help="verify bot IPs against published ranges (needs network)")
    args = ap.parse_args()

    paths = []
    for pattern in args.logs:
        paths += glob.glob(pattern)
    if not paths:
        sys.exit("no log files matched")

    tokens = load_registry(args.bots)
    stats = defaultdict(lambda: {
        "hits": 0, "statuses": Counter(), "paths": Counter(),
        "ips": Counter(), "first": None, "last": None, "durations": [],
    })
    total_lines = 0

    for rec in iter_records(paths, args.format):
        total_lines += 1
        ua = rec["ua"]
        ua_l = ua.lower()
        for tok_l, meta in tokens.items():
            if tok_l in ua_l:
                s = stats[meta["token"]]
                s["hits"] += 1
                s["statuses"][rec["status"]] += 1
                s["paths"][rec["path"]] += 1
                if rec["ip"]:
                    s["ips"][rec["ip"]] += 1
                if rec.get("duration"):
                    s["durations"].append(float(rec["duration"]))
                t = rec.get("time")
                if t:
                    s["first"] = min(s["first"], t) if s["first"] else t
                    s["last"] = max(s["last"], t) if s["last"] else t
                break

    verified = {}
    if args.verify:
        for token in stats:
            src = VERIFY_SOURCES.get(token)
            if not src:
                continue
            nets = fetch_ranges(src)
            if not nets:
                continue
            good = bad = 0
            for ip, count in stats[token]["ips"].items():
                try:
                    addr = ipaddress.ip_address(ip)
                    if any(addr in n for n in nets):
                        good += count
                    else:
                        bad += count
                except ValueError:
                    bad += count
            verified[token] = {"verified_hits": good, "unverified_hits": bad}

    # ---- report
    lines = [
        "# AI Bot Log Analysis",
        f"\nParsed **{total_lines:,}** log records from {len(paths)} file(s).\n",
        "| Bot | Category | Hits | 2xx | 3xx | 4xx | 499 | 5xx | Verified IPs | First seen | Last seen |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    order = {"retrieval": 0, "user_fetch": 1, "training": 2}
    cat_of = {m["token"]: m["category"] for m in tokens.values()}
    for token in sorted(stats, key=lambda t: (order.get(cat_of.get(t, ""), 9), -stats[t]["hits"])):
        s = stats[token]
        st = s["statuses"]
        c2 = sum(v for k, v in st.items() if 200 <= k < 300)
        c3 = sum(v for k, v in st.items() if 300 <= k < 400)
        c499 = st.get(499, 0)
        c4 = sum(v for k, v in st.items() if 400 <= k < 500) - c499
        c5 = sum(v for k, v in st.items() if k >= 500)
        v = verified.get(token)
        vtxt = f"{v['verified_hits']}/{s['hits']}" if v else "—"
        lines.append(f"| {token} | {cat_of.get(token, '?')} | {s['hits']} | {c2} | {c3} "
                     f"| {c4} | **{c499}** | {c5} | {vtxt} | {s['first'] or '—'} | {s['last'] or '—'} |")

    if not stats:
        lines.append("\n**No AI bot traffic found.** Either the site gets no AI crawler "
                     "attention yet (a visibility problem in itself) or these logs don't "
                     "cover edge/static requests — Vercel runtime logs only include "
                     "function invocations; use a Log Drain for full coverage.")

    problems = []
    for token, s in stats.items():
        errs = sum(v for k, v in s["statuses"].items() if k >= 400)
        if s["hits"] and errs / s["hits"] > 0.05:
            problems.append(f"- **{token}**: {errs}/{s['hits']} requests errored "
                            f"({dict(s['statuses'])}) — every one is a lost citation opportunity")
        if s["statuses"].get(499):
            problems.append(f"- **{token}**: {s['statuses'][499]} × 499 — the bot gave up "
                            f"waiting. Fix TTFB on the affected paths.")
    if problems:
        lines.append("\n## Problems\n")
        lines += problems

    lines.append("\n## Top crawled paths per bot\n")
    for token, s in sorted(stats.items(), key=lambda kv: -kv[1]["hits"]):
        top = ", ".join(f"`{p}` ({n})" for p, n in s["paths"].most_common(5))
        lines.append(f"- **{token}**: {top}")

    report = "\n".join(lines)
    os.makedirs(args.out, exist_ok=True)
    out_md = os.path.join(args.out, "bot_log_report.md")
    with open(out_md, "w") as fh:
        fh.write(report)
    with open(os.path.join(args.out, "bot_log_stats.json"), "w") as fh:
        json.dump({t: {"hits": s["hits"], "statuses": dict(s["statuses"]),
                       "top_paths": s["paths"].most_common(10),
                       "verified": verified.get(t)} for t, s in stats.items()}, fh, indent=2)
    print(report)
    print(f"\nWrote {out_md}")


if __name__ == "__main__":
    main()
