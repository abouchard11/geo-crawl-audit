#!/usr/bin/env python3
"""
geo_probe.py — Active GEO crawl audit.

Probes each domain with the user-agents of the AI crawlers that matter
(training / retrieval / user-fetch), measures status + TTFB, detects
WAF/bot-management differentials vs a baseline browser UA, analyzes
whether content exists in the baseline raw HTML response, and
parses robots.txt handling of AI bot tokens.

Zero third-party dependencies: uses curl subprocess for precise timing
(%{json} write-out) and Python stdlib for everything else.

Usage:
  python3 geo_probe.py example.com another.com --out ./audit-results
  python3 geo_probe.py --domains-file domains.txt --out ./audit-results

Caveat baked into the method: probes originate from YOUR machine's IP,
not the bot's published ranges. A WAF doing verified-bot IP checks may
block our simulated bot (fake-bot detection) while allowing the real
one — or allow us while IP-blocking the real one. A differential result
therefore means "bot-sensitive filtering layer present — confirm with
server logs (drain_parser.py)", not a definitive verdict.
"""

import argparse
import concurrent.futures
import html as html_lib
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CURL_TIMEOUT = 25
CONNECT_TIMEOUT = 8
INTER_REQUEST_DELAY = 0.35

# ---------------------------------------------------------------- curl layer


def curl_fetch(url, ua, save_body=False, max_time=CURL_TIMEOUT):
    """Fetch a URL with curl, returning timing/status/header data."""
    body_path = None
    hdr_fd, hdr_path = tempfile.mkstemp(suffix=".hdrs")
    os.close(hdr_fd)
    if save_body:
        body_fd, body_path = tempfile.mkstemp(suffix=".body")
        os.close(body_fd)
    out_target = body_path if save_body else os.devnull

    cmd = [
        "curl", "-sS", "-L", "--compressed",
        "--max-time", str(max_time),
        "--connect-timeout", str(CONNECT_TIMEOUT),
        "-A", ua,
        "-o", out_target,
        "-D", hdr_path,
        "-w", "%{json}",
        url,
    ]
    result = {"url": url, "ok": False, "error": None}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max_time + 10)
        if proc.stdout.strip():
            # curl may emit multiple JSON write-outs on redirect in old
            # versions; take the last JSON object.
            raw = proc.stdout.strip().splitlines()[-1]
            w = json.loads(raw)
            result.update({
                "ok": True,
                "status": w.get("http_code", 0),
                "ttfb": round(w.get("time_starttransfer", 0.0), 3),
                "connect": round(w.get("time_connect", 0.0), 3),
                "tls": round(w.get("time_appconnect", 0.0), 3),
                "total": round(w.get("time_total", 0.0), 3),
                "size": int(w.get("size_download", 0)),
                "redirects": int(w.get("num_redirects", 0)),
                "final_url": w.get("url_effective", url),
            })
        if proc.returncode != 0 and not result["ok"]:
            result["error"] = (proc.stderr or f"curl exit {proc.returncode}").strip()[:200]
    except subprocess.TimeoutExpired:
        result["error"] = "hard timeout"
    except (json.JSONDecodeError, ValueError) as exc:
        result["error"] = f"write-out parse: {exc}"

    # Headers (from the final response in the chain)
    headers = {}
    try:
        with open(hdr_path, "r", errors="replace") as fh:
            blocks = fh.read().strip().split("\r\n\r\n")
            last = blocks[-1] if blocks else ""
            for line in last.splitlines()[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
    except OSError:
        pass
    finally:
        os.unlink(hdr_path)
    result["headers"] = headers

    body = ""
    if save_body and body_path:
        try:
            with open(body_path, "r", errors="replace") as fh:
                body = fh.read()
        except OSError:
            pass
        finally:
            os.unlink(body_path)
    result["body"] = body
    return result


def challenge_signals(resp):
    """Detect bot-challenge/mitigation markers in a response."""
    signals = []
    h = resp.get("headers", {})
    status = resp.get("status", 0)
    if h.get("cf-mitigated") == "challenge":
        signals.append("cloudflare-challenge")
    if status in (403, 429, 503) and "cloudflare" in h.get("server", ""):
        signals.append(f"cloudflare-{status}")
    if "x-vercel-mitigated" in h:
        signals.append("vercel-mitigated")
    if status == 429 and "vercel" in h.get("server", ""):
        signals.append("vercel-429")
    return signals


# ------------------------------------------------------------ content layer


def analyze_content(body):
    """Classify the text present in one raw HTML response.

    This is a useful non-rendering baseline, not proof that every crawler
    receives the same HTML or that a vendor never renders JavaScript.
    """
    if not body:
        return {"classification": "EMPTY", "visible_words": 0}

    work = re.sub(r"<script\b[^>]*>.*?</script>", " ", body, flags=re.S | re.I)
    work = re.sub(r"<style\b[^>]*>.*?</style>", " ", work, flags=re.S | re.I)
    work = re.sub(r"<!--.*?-->", " ", work, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", work)
    text = html_lib.unescape(re.sub(r"\s+", " ", text)).strip()
    words = len(text.split())

    title_m = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.S | re.I)
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S | re.I)
    json_ld = len(re.findall(r'type=["\']application/ld\+json["\']', body, flags=re.I))

    if words >= 400:
        cls = "SSR_FULL"
    elif words >= 150:
        cls = "SSR_THIN"
    else:
        cls = "CSR_SHELL"

    return {
        "classification": cls,
        "visible_words": words,
        "html_bytes": len(body),
        "title": html_lib.unescape(re.sub(r"<[^>]+>", "", title_m.group(1)).strip())[:120] if title_m else None,
        "h1_count": len(h1s),
        "first_h1": html_lib.unescape(re.sub(r"<[^>]+>", "", h1s[0]).strip())[:120] if h1s else None,
        "json_ld_blocks": json_ld,
        "has_next_data": "__NEXT_DATA__" in body,
    }


# ------------------------------------------------------------- robots layer


def parse_robots(body):
    """Parse robots.txt into {agent_lower: [(directive, path), ...]} + sitemaps."""
    groups, sitemaps = {}, []
    current_agents, expecting_agents = [], True
    if not body or body.lstrip()[:1] == "<":
        return None, []  # missing or HTML error page served as robots.txt
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = [p.strip() for p in line.split(":", 1)]
        field = field.lower()
        if field == "sitemap":
            sitemaps.append(value)
        elif field == "user-agent":
            if not expecting_agents:
                current_agents = []
            expecting_agents = True
            current_agents.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif field in ("allow", "disallow"):
            expecting_agents = False
            for agent in current_agents:
                groups[agent].append((field, value))
    return groups, sitemaps


def robots_path_matches(pattern, request_path="/"):
    """Return whether a robots path pattern matches ``request_path``."""
    if pattern == "":
        return False
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    expr = "^" + re.escape(pattern).replace(r"\*", ".*")
    if anchored:
        expr += "$"
    return re.search(expr, request_path) is not None


def robots_verdict(groups, token):
    """Root-path access verdict for a bot token: (allowed, explicit_block)."""
    if groups is None:
        return True, False  # no robots.txt -> everything allowed
    tl = token.lower()
    rules = groups.get(tl)
    explicit = rules is not None
    if rules is None:
        rules = groups.get("*", [])
    # Longest-match wins; Allow wins ties. Empty Disallow means allow-all.
    best_len, allowed = -1, True
    for directive, path in rules:
        if path == "" and directive == "disallow":
            continue
        if robots_path_matches(path):
            match_len = len(path.rstrip("$"))
            candidate_allowed = directive == "allow"
            if match_len > best_len or (match_len == best_len and candidate_allowed):
                best_len = match_len
                allowed = candidate_allowed
    return allowed, explicit


# -------------------------------------------------------------- audit layer


def audit_domain(domain, registry, sample_pages=0):
    base_url = domain if domain.startswith("http") else f"https://{domain}"
    baseline_ua = registry["baseline"]["ua"]
    probe_bots = [b for b in registry["bots"] if b.get("probe")]
    token_only = [b for b in registry["bots"] if b.get("robots_token_only")]

    out = {"domain": domain, "probes": {}, "flags": []}

    # 1) Baseline, twice. The first/repeat gap is a variability signal; a first
    #    request is not automatically a CDN miss or serverless cold start.
    cold = curl_fetch(base_url, baseline_ua, save_body=False)
    time.sleep(INTER_REQUEST_DELAY)
    warm = curl_fetch(cold.get("final_url", base_url), baseline_ua, save_body=True)
    if not warm.get("ok") or warm.get("status", 0) == 0:
        out["error"] = warm.get("error") or cold.get("error") or "unreachable"
        return out
    out["baseline"] = {
        "first_ttfb": cold.get("ttfb"), "repeat_ttfb": warm.get("ttfb"),
        # Backward-compatible aliases retained for v0.1 JSON consumers.
        "cold_ttfb": cold.get("ttfb"), "warm_ttfb": warm.get("ttfb"),
        "status": warm.get("status"), "final_url": warm.get("final_url"),
        "server": warm["headers"].get("server"),
        "cache": warm["headers"].get("x-vercel-cache") or warm["headers"].get("cf-cache-status"),
        "size": warm.get("size"),
    }
    final_url = warm.get("final_url", base_url)

    # 2) Raw-HTML content analysis of the baseline response.
    out["content"] = analyze_content(warm.get("body", ""))

    # 3) robots.txt + llms.txt
    time.sleep(INTER_REQUEST_DELAY)
    robots_resp = curl_fetch(f"{base_url.rstrip('/')}/robots.txt", baseline_ua, save_body=True)
    groups, sitemaps = (None, [])
    if robots_resp.get("status") == 200:
        groups, sitemaps = parse_robots(robots_resp.get("body", ""))
    out["robots"] = {
        "status": robots_resp.get("status"),
        "sitemaps": sitemaps,
        "bots": {},
    }
    for bot in probe_bots + token_only:
        allowed, explicit = robots_verdict(groups, bot["token"])
        out["robots"]["bots"][bot["token"]] = {"allowed": allowed, "explicit": explicit}

    time.sleep(INTER_REQUEST_DELAY)
    llms = curl_fetch(f"{base_url.rstrip('/')}/llms.txt", baseline_ua, save_body=True)
    body_l = llms.get("body", "")
    out["llms_txt"] = bool(
        llms.get("status") == 200 and body_l and body_l.lstrip()[:1] != "<"
    )

    # 4) Bot UA probes against the warm origin
    baseline_status = warm.get("status")
    ttfbs = []
    for bot in probe_bots:
        time.sleep(INTER_REQUEST_DELAY)
        resp = curl_fetch(final_url, bot["ua"], save_body=False)
        if not resp.get("status"):
            # status 0 = transport-level failure (timeout/reset). Could be a
            # transient network blip OR aggressive connection-level blocking.
            # Never flag off a single sample — retry before concluding.
            time.sleep(1.0)
            resp = curl_fetch(final_url, bot["ua"], save_body=False)
        sig = challenge_signals(resp)
        entry = {
            "status": resp.get("status"), "ttfb": resp.get("ttfb"),
            "size": resp.get("size"), "error": resp.get("error"),
            "challenge": sig, "category": bot["category"],
        }
        # Differential logic: status mismatch vs baseline, challenge marker,
        # or a body dramatically smaller than baseline (challenge page).
        # Transport failures that survived a retry are reported separately —
        # they may be connection-level blocking but are not proven
        # differentials, and conflating them destroys trust in the tool.
        differential = None
        if not resp.get("status"):
            entry["probe_error"] = resp.get("error") or "connection failed after retry"
        elif resp.get("status") != baseline_status:
            differential = f"status {resp.get('status')} vs baseline {baseline_status}"
        elif sig:
            differential = ",".join(sig)
        elif warm.get("size") and resp.get("size") is not None and \
                resp["size"] < warm["size"] * 0.25:
            differential = f"body {resp['size']}B vs baseline {warm['size']}B"
        entry["differential"] = differential
        out["probes"][bot["token"]] = entry
        if resp.get("ttfb"):
            ttfbs.append(resp["ttfb"])

    out["bot_ttfb_median"] = round(statistics.median(ttfbs), 3) if ttfbs else None
    out["bot_ttfb_max"] = round(max(ttfbs), 3) if ttfbs else None

    # 5) Score + flags
    score_and_flag(out, probe_bots)
    return out


def score_and_flag(out, probe_bots):
    flags, score = out["flags"], 100

    # If even the baseline browser UA couldn't get a clean 200, everything
    # downstream (content classification, differentials) describes an error
    # page, not the site. Common cause: the probe environment itself (cloud
    # datacenter IP, curl TLS fingerprint) being filtered. Say so loudly
    # rather than publishing a wrong verdict.
    baseline_ok = out.get("baseline", {}).get("status") == 200
    if not baseline_ok:
        flags.append({
            "severity": "WARN", "code": "BASELINE_ANOMALY",
            "detail": f"baseline browser fetch returned "
                      f"{out['baseline'].get('status')} — results likely reflect "
                      f"probe-environment filtering, not real bot experience; "
                      f"re-run from a residential network before concluding anything",
        })
        out["conclusive"] = False
        out["score"] = None
        return
    out["conclusive"] = True

    # Reachability (max -40)
    reach_penalty = 0
    for bot in probe_bots:
        p = out["probes"].get(bot["token"], {})
        if p.get("probe_error"):
            flags.append({
                "severity": "WARN",
                "code": "PROBE_ERROR",
                "detail": f"{bot['token']}: {p['probe_error']} (twice) — could be transient "
                          f"network or connection-level bot blocking; check logs, re-run to confirm",
            })
            continue
        if p.get("differential"):
            sev = 10 if bot["category"] in ("retrieval", "user_fetch") else 5
            reach_penalty += sev
            flags.append({
                "severity": "CRITICAL" if sev == 10 else "HIGH",
                "code": "BOT_DIFFERENTIAL",
                "detail": f"{bot['token']}: {p['differential']} — bot-sensitive filtering; confirm with logs",
            })
    score -= min(reach_penalty, 40)

    # Speed (max -25). Thresholds are audit heuristics, not vendor SLAs.
    med = out.get("bot_ttfb_median")
    cold = out.get("baseline", {}).get("cold_ttfb")
    if med is not None:
        if med > 2.0:
            score -= 25
            flags.append({"severity": "CRITICAL", "code": "SLOW_TTFB",
                          "detail": f"median simulated-UA TTFB {med}s — investigate timeout risk in logs"})
        elif med > 1.2:
            score -= 15
            flags.append({"severity": "HIGH", "code": "SLOW_TTFB",
                          "detail": f"median bot TTFB {med}s"})
        elif med > 0.8:
            score -= 7
    if cold and med and cold > max(2.0, med * 3):
        flags.append({"severity": "HIGH", "code": "TTFB_VARIANCE",
                      "detail": f"first TTFB {cold}s vs repeat {out['baseline']['repeat_ttfb']}s — "
                                f"confirm cache/origin behavior with response headers and logs"})

    # Raw-HTML content (max -25) — skipped when the baseline itself failed,
    # because we'd be classifying an error page's word count.
    cls = out.get("content", {}).get("classification") if baseline_ok else None
    if cls == "CSR_SHELL" or cls == "EMPTY":
        score -= 25
        flags.append({"severity": "CRITICAL", "code": "CSR_SHELL",
                      "detail": f"baseline raw HTML contains only "
                                f"{out['content'].get('visible_words', 0)} visible words — "
                                f"non-rendering clients may miss client-rendered content; "
                                f"check bot-specific responses and logs"})
    elif cls == "SSR_THIN":
        score -= 12
        flags.append({"severity": "WARN", "code": "THIN_HTML",
                      "detail": f"{out['content']['visible_words']} visible words — thin for passage retrieval"})

    # robots.txt (max -10)
    rb = out.get("robots", {})
    if rb.get("status") != 200:
        score -= 5
        flags.append({"severity": "WARN", "code": "NO_ROBOTS", "detail": "robots.txt missing or erroring"})
    else:
        blocked = [t for t, v in rb.get("bots", {}).items() if not v["allowed"]]
        if blocked:
            score -= 5
            flags.append({"severity": "HIGH", "code": "ROBOTS_BLOCKS",
                          "detail": f"robots.txt blocks: {', '.join(blocked)}"})
        if not rb.get("sitemaps"):
            score -= 3
            flags.append({"severity": "WARN", "code": "NO_SITEMAP", "detail": "no Sitemap: line in robots.txt"})
        retrieval_tokens = [b["token"] for b in probe_bots if b["category"] == "retrieval"]
        implicit = [t for t in retrieval_tokens
                    if rb["bots"].get(t) and rb["bots"][t]["allowed"] and not rb["bots"][t]["explicit"]]
        if implicit:
            flags.append({"severity": "INFO", "code": "IMPLICIT_ALLOW",
                          "detail": f"retrieval bots allowed only via wildcard (add explicit blocks): {', '.join(implicit)}"})

    if not out.get("llms_txt"):
        flags.append({"severity": "INFO", "code": "NO_LLMS_TXT",
                      "detail": "no llms.txt (near-zero evidence of impact; lowest priority)"})

    out["score"] = max(score, 0)


# -------------------------------------------------------------- report layer


SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "WARN": 2, "INFO": 3}


def render_report(results, generated_at):
    lines = [
        "# GEO Crawl Audit",
        f"\n**Generated:** {generated_at}  ",
        "**Method:** active multi-UA probe (see caveat at bottom)\n",
        "## Portfolio scorecard\n",
        "| Domain | Score | Raw HTML | Words | Repeat TTFB | First TTFB | Simulated-UA TTFB (med) | Differentials | Sitemap |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    ok = [r for r in results if "error" not in r]
    for r in sorted(ok, key=lambda x: x["score"] if isinstance(x.get("score"), int) else -1):
        diffs = sum(1 for p in r["probes"].values() if p.get("differential"))
        score = f"**{r['score']}**" if isinstance(r.get("score"), int) else "INCONCLUSIVE"
        lines.append(
            f"| {r['domain']} | {score} | {r['content']['classification']} "
            f"| {r['content']['visible_words']} | {r['baseline']['repeat_ttfb']}s "
            f"| {r['baseline']['first_ttfb']}s | {r.get('bot_ttfb_median')}s "
            f"| {diffs or '—'} | {'✓' if r['robots'].get('sitemaps') else '✗'} |"
        )
    for r in results:
        if "error" in r:
            lines.append(f"| {r['domain']} | — | UNREACHABLE: {r['error']} | | | | | | |")

    all_flags = []
    for r in ok:
        for f in r["flags"]:
            if f["severity"] != "INFO":
                all_flags.append((f["severity"], r["domain"], f["code"], f["detail"]))
    all_flags.sort(key=lambda x: SEV_ORDER[x[0]])
    if all_flags:
        lines.append("\n## Flags (worst first)\n")
        for sev, dom, code, detail in all_flags:
            lines.append(f"- **[{sev}] {dom}** `{code}` — {detail}")

    lines.append("\n## Per-domain detail\n")
    for r in sorted(ok, key=lambda x: x["score"] if isinstance(x.get("score"), int) else -1):
        c, b = r["content"], r["baseline"]
        score_label = f"{r['score']}/100" if isinstance(r.get("score"), int) else "inconclusive"
        lines += [
            f"### {r['domain']} — {score_label}\n",
            f"- Final URL: {b['final_url']} · server: `{b.get('server')}` · cache: `{b.get('cache')}`",
            f"- Title: {c.get('title')!r} · H1: {c.get('first_h1')!r} · JSON-LD blocks: {c.get('json_ld_blocks')}",
            f"- llms.txt: {'yes' if r.get('llms_txt') else 'no'} · sitemaps: {len(r['robots'].get('sitemaps', []))}",
            "",
            "| Bot | Cat | Status | TTFB | Differential |",
            "|---|---|---|---|---|",
        ]
        for token, p in r["probes"].items():
            lines.append(f"| {token} | {p['category']} | {p['status']} | {p['ttfb']}s "
                         f"| {p.get('differential') or '—'} |")
        lines.append("")

    lines += [
        "\n---\n### Method caveat",
        "Probes are sent from this machine's IP with simulated bot user-agents. "
        "WAFs that verify bots by IP range may treat the simulation differently "
        "than the real crawler (in either direction). A differential here means "
        "*a bot-sensitive filtering layer exists* — confirm actual bot outcomes "
        "with server logs via `drain_parser.py`.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description="Active GEO crawl audit")
    ap.add_argument("domains", nargs="*", help="domains to audit")
    ap.add_argument("--domains-file", help="file with one domain per line")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--bots", default=os.path.join(HERE, "bots.json"))
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args()

    domains = list(args.domains)
    if args.domains_file:
        with open(args.domains_file) as fh:
            domains += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not domains:
        ap.error("no domains given")

    with open(args.bots) as fh:
        registry = json.load(fh)

    os.makedirs(args.out, exist_ok=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(audit_domain, d, registry): d for d in domains}
        for fut in concurrent.futures.as_completed(futures):
            r = fut.result()
            results.append(r)
            state = f"score {r.get('score')}" if "error" not in r else f"ERROR {r['error']}"
            print(f"  [{len(results)}/{len(domains)}] {r['domain']}: {state}", file=sys.stderr)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    results.sort(key=lambda r: r.get("score") if isinstance(r.get("score"), int) else -1)
    json_path = os.path.join(args.out, "geo_audit.json")
    md_path = os.path.join(args.out, "geo_audit_report.md")
    with open(json_path, "w") as fh:
        json.dump({"generated_at": generated_at, "results": results}, fh, indent=2)
    with open(md_path, "w") as fh:
        fh.write(render_report(results, generated_at))
    print(f"\nWrote {json_path}\nWrote {md_path}")


if __name__ == "__main__":
    main()
