---
name: vibe-coding-news
description: Daily developer-focused briefing on vibe coding and AI coding tools (Claude Code, Codex, Cursor, Copilot, Gemini CLI, MCP, coding agents). Collects from GitHub, Hacker News, Lobsters, Techmeme, Simon Willison, dev.to and Hugging Face papers with no API keys, saves sources and images, links every item to the primary source and a download link, and optionally drafts social posts in the user's own writing style. Use when the user asks for AI coding news, a vibe coding digest, "what's new in coding agents", or social post drafts about those news.
license: MIT
---

# Vibe Coding News

Produce one dated briefing file (plus optional post drafts) about the last 24 hours in AI-assisted coding, written for developers.

Write everything in the user's language (the language they talk to you in), unless `config.json` sets `language`.

## 0. Setup (first run only)

1. Pick an output folder. Default: `./vibe-news/` in the current working directory. If `config.json` exists next to this file, read `output_dir`, `language`, `keywords`, `style_guide` and any source overrides from it (see `config.example.json`).
2. Python 3.8+ is the only requirement. `gh` (GitHub CLI) is optional; when logged in it raises GitHub rate limits.

## 1. Collect

Run the collector first. It hits every source in one go and never needs a key:

```bash
python3 scripts/collect.py --hours 24 --out <output_dir>/raw-YYYY-MM-DD.json [--config config.json]
```

It prints counts and an `errors` list. Sources in `errors` go into the briefing's "Coverage limits" line as unverified; do not silently drop them.

What it gathers:
- **GitHub**: new repos (last 24h) by stars for coding-agent keywords; latest releases of Claude Code, Codex, Gemini CLI, Cline, Continue, MCP servers.
- **Hacker News** (Algolia API): stories above 20 points per keyword, with discussion links.
- **Lobsters** (ai, vibecoding tags), **Techmeme** RSS, **Simon Willison** Atom, **dev.to** top posts, **Hugging Face** daily papers.

Then fill gaps with web search (run several searches in parallel) for official blogs and changelogs of the tools that appear, and open the key articles to read them.

Known blockers, so you don't waste retries:
- Reddit returns 429 quickly and Bluesky's public API returns 403. Skip them.
- microsoft.com, npmjs.com and sec.gov return 403 to scripts. That is bot-blocking, not a dead link. Use `npm view <pkg> version` for npm, or a browser tool if one is available.
- Pages rendered by JavaScript (for example Microsoft Tech Community) come back empty from plain fetches. Use a browser tool, or cite the secondary article and mark the primary as not opened.

## 2. Decide what matters

- Rank by impact on working developers: security issues in tools people run locally, breaking or pricing changes, new capabilities in major agents, then industry moves (funding, IPOs, lawsuits) and community debates.
- Remove duplicates, ads and rumors. Mark anything you could not confirm as **unverified**.
- **Primary source rule**: if you only have a secondary article (news site), open it and follow its link to the official post, release or paper. Link the primary.
- Summarize in your own words. At most one short quote.

## 3. Links (every item, no exceptions)

- Always full URLs with `https://`.
- Each item gets `Source https://...` and `Download https://...`. Add `Sign up https://...` or `Web https://...` when relevant.
- Download order: official store or install page → GitHub `/releases/latest` → npm/pip package page. For a news story, link the download of the tool it is about. If nothing exists, write `Download: none (reason)`.
- Check links: `python3 scripts/media.py check <url> ...`. `blocked` is fine to keep; `dead` must be replaced.

## 4. Images

For each top item and major release:

```bash
python3 scripts/media.py image <article-url> <output_dir>/images/YYYY-MM-DD/NN-source-keyword
```

It saves the og:image, rejects files over 5 MB and non-images. Put the image in the briefing with a caption naming the outlet and the source URL. Images are for the user's private reference; tell them not to republish without rights.

## 5. Write the briefing

Save as `<output_dir>/YYYY-MM-DD.md` using `templates/briefing.md`. Sections:

1. Coverage limits (sources that failed, things not opened)
2. One-line summary of the day
3. Top 5: title, what happened, what it means for developers, image + caption, Source / Download
4. New tools, models, features (versions, price changes)
5. Security and quality
6. GitHub: top new repos (stars), tool releases
7. Community: top HN stories (points, comments, discussion link), Lobsters, dev.to, mood in one paragraph
8. Try this: 1–3 concrete things the user could test, fitted to their stack if you know it
9. Follow-ups: items that continue an earlier day's story (check yesterday's file)
10. Sources table: # / outlet / title / URL / date

## 6. Post drafts (optional)

Only if the user wants social posts. Draft 3 posts, one issue each, from the freshest high-impact items of the last 24 hours (widen to 48h only if needed; never repeat yesterday's topics). Format per `templates/post.md`: 3–6 lines of summary, 1–2 lines of the user's own take, a blank line, then Source and Download lines.

Match the user's voice. If `style_guide` points to a file, follow it. If there is none, offer to build one with `references/style-learning.md` from the user's own past posts.

Save to `<output_dir>/drafts-YYYY-MM-DD.md`. **Never post anything yourself.** The user publishes.

## 7. Report

Reply with three lines on what mattered most, the file paths, and how many images were saved. No other side effects: no posting, emailing, deploying or purchasing.

## Checklist

- [ ] Ran `collect.py` and listed its `errors` as coverage limits
- [ ] Primary sources, not just news articles
- [ ] Every link starts with `https://`, every item has a Download line
- [ ] Links checked; no `dead`
- [ ] Images saved with outlet + URL captions
- [ ] Drafts (if any): 3 posts, one issue each, last 24h, user's voice, not posted
