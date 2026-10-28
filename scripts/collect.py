#!/usr/bin/env python3
"""Collect recent AI-coding / vibe-coding signals from public sources.

Standard library only. No API keys required (uses `gh` for GitHub if it is
installed and logged in, otherwise the unauthenticated GitHub REST API).

Usage:
  python3 collect.py --hours 24 --out raw.json
  python3 collect.py --config config.json --out raw.json
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

UA = "Mozilla/5.0 (compatible; vibe-coding-news/1.0)"

DEFAULTS = {
    "keywords": [
        "vibe coding", "claude code", "codex", "cursor", "copilot",
        "gemini cli", "mcp", "coding agent", "agentic coding",
    ],
    "github_search": ["vibe coding", "claude code", "mcp server", "coding agent", "cursor rules"],
    "github_repos": [
        "anthropics/claude-code", "openai/codex", "google-gemini/gemini-cli",
        "cline/cline", "continuedev/continue", "modelcontextprotocol/servers",
    ],
    "lobsters_tags": ["ai", "vibecoding"],
    "devto_tags": ["ai", "claude", "mcp", "vibecoding"],
    "hn_min_points": 20,
}


def http_get(url, accept="*/*", retries=3):
    """GET with backoff on 429/5xx. Returns bytes or raises."""
    delay = 3
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def get_json(url):
    return json.loads(http_get(url, accept="application/json"))


def gh_api(path, params=None):
    """GitHub API via `gh` when available (higher rate limit), else plain HTTP."""
    params = params or {}
    if shutil.which("gh"):
        cmd = ["gh", "api", "-X", "GET", path]
        for k, v in params.items():
            cmd += ["-f", f"{k}={v}"]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return json.loads(out.stdout)
    qs = ("?" + urllib.parse.urlencode(params)) if params else ""
    return get_json(f"https://api.github.com/{path.lstrip('/')}{qs}")


def section(name, fn, errors):
    try:
        return fn()
    except Exception as e:  # keep going: one dead source must not kill the run
        errors.append({"source": name, "error": f"{type(e).__name__}: {e}"})
        return []


def collect_github(cfg, since):
    day = since.strftime("%Y-%m-%d")
    repos, seen = [], set()
    for kw in cfg["github_search"]:
        data = gh_api("search/repositories", {
            "q": f"{kw} created:>={day}", "sort": "stars", "order": "desc", "per_page": 10})
        for it in data.get("items", []):
            if it["full_name"] in seen:
                continue
            seen.add(it["full_name"])
            repos.append({
                "name": it["full_name"], "url": it["html_url"], "stars": it["stargazers_count"],
                "description": it.get("description"), "language": it.get("language"),
                "created": it["created_at"], "keyword": kw,
                "download": it["html_url"] + "/releases/latest",
            })
        time.sleep(1)
    repos.sort(key=lambda r: r["stars"], reverse=True)

    releases = []
    for full in cfg["github_repos"]:
        for rel in gh_api(f"repos/{full}/releases", {"per_page": 3}):
            published = rel.get("published_at") or ""
            releases.append({
                "repo": full, "tag": rel["tag_name"], "name": rel.get("name"),
                "url": rel["html_url"], "published": published,
                "recent": published >= since.isoformat()[:19],
                "body": (rel.get("body") or "")[:1500],
            })
        time.sleep(0.5)
    return {"new_repos": repos[:20], "releases": releases}


def collect_hn(cfg, since):
    ts = int(since.timestamp())
    hits, seen = [], set()
    for kw in cfg["keywords"]:
        q = urllib.parse.urlencode({
            "query": kw, "tags": "story",
            "numericFilters": f"created_at_i>{ts},points>{cfg['hn_min_points']}"})
        for h in get_json(f"https://hn.algolia.com/api/v1/search?{q}").get("hits", []):
            if h["objectID"] in seen:
                continue
            seen.add(h["objectID"])
            hits.append({
                "title": h.get("title"), "url": h.get("url"), "points": h.get("points"),
                "comments": h.get("num_comments"), "created": h.get("created_at"),
                "discussion": f"https://news.ycombinator.com/item?id={h['objectID']}", "keyword": kw,
            })
    hits.sort(key=lambda h: h["points"] or 0, reverse=True)
    return hits[:30]


def collect_lobsters(cfg, since):
    tags = ",".join(cfg["lobsters_tags"])
    out = []
    for s in get_json(f"https://lobste.rs/t/{tags}.json"):
        if s.get("created_at", "") < since.isoformat()[:19]:
            continue
        out.append({"title": s["title"], "url": s.get("url") or s["short_id_url"],
                    "score": s.get("score"), "comments": s.get("comment_count"),
                    "discussion": s.get("comments_url"), "tags": s.get("tags"), "created": s["created_at"]})
    return out


def parse_feed(raw, limit=30):
    """RSS 2.0 or Atom -> [{title, url, published}]"""
    # Feeds never need a DTD; refusing one blocks entity-expansion tricks.
    if b"<!DOCTYPE" in raw[:2048].upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("feed contains DOCTYPE/ENTITY, refused")
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = []
    for it in root.iter("item"):
        items.append({"title": it.findtext("title"), "url": it.findtext("link"),
                      "published": it.findtext("pubDate")})
    for e in root.findall("a:entry", ns):
        link = e.find("a:link", ns)
        items.append({"title": e.findtext("a:title", namespaces=ns),
                      "url": link.get("href") if link is not None else None,
                      "published": e.findtext("a:published", namespaces=ns) or e.findtext("a:updated", namespaces=ns)})
    return items[:limit]


def collect_feeds(cfg, since):
    feeds = {
        "techmeme": "https://www.techmeme.com/feed.xml",
        "simonwillison": "https://simonwillison.net/atom/everything/",
    }
    feeds.update(cfg.get("extra_feeds", {}))
    return {name: parse_feed(http_get(url)) for name, url in feeds.items()}


def collect_devto(cfg, since):
    out, seen = [], set()
    for tag in cfg["devto_tags"]:
        for a in get_json(f"https://dev.to/api/articles?tag={tag}&top=1&per_page=10"):
            if a["id"] in seen:
                continue
            seen.add(a["id"])
            out.append({"title": a["title"], "url": a["url"], "reactions": a.get("public_reactions_count"),
                        "comments": a.get("comments_count"), "published": a.get("published_at"), "tag": tag})
    out.sort(key=lambda a: a["reactions"] or 0, reverse=True)
    return out[:15]


def collect_papers(cfg, since):
    return [{"title": p.get("title"), "url": f"https://huggingface.co/papers/{p.get('paper', {}).get('id', '')}",
             "upvotes": p.get("paper", {}).get("upvotes")}
            for p in get_json("https://huggingface.co/api/daily_papers?limit=20")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--config", help="JSON file overriding DEFAULTS")
    ap.add_argument("--out", help="write JSON here (default: stdout)")
    args = ap.parse_args()

    cfg = dict(DEFAULTS)
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            cfg.update(json.load(f))

    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    errors = []
    result = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "since": since.isoformat(),
        "github": section("github", lambda: collect_github(cfg, since), errors),
        "hackernews": section("hackernews", lambda: collect_hn(cfg, since), errors),
        "lobsters": section("lobsters", lambda: collect_lobsters(cfg, since), errors),
        "feeds": section("feeds", lambda: collect_feeds(cfg, since), errors),
        "devto": section("devto", lambda: collect_devto(cfg, since), errors),
        "papers": section("papers", lambda: collect_papers(cfg, since), errors),
    }
    result["errors"] = errors

    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        counts = {k: (len(v) if isinstance(v, list) else {kk: len(vv) for kk, vv in v.items()})
                  for k, v in result.items() if k not in ("collected_at", "since", "errors")}
        print(json.dumps({"out": args.out, "counts": counts, "errors": errors}, ensure_ascii=False))
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
