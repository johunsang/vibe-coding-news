#!/usr/bin/env python3
"""Link checks and article images. Standard library only.

  python3 media.py check <url> [<url> ...]
      -> prints status per URL. 403 from bot-blocking sites (microsoft.com,
         npmjs.com, sec.gov) is reported as "blocked", not "dead".

  python3 media.py image <article-url> <out-path-without-extension>
      -> finds og:image / twitter:image, downloads it, checks the magic bytes,
         and prints the saved path (or the image URL if download failed).
"""
import json
import re
import sys
import urllib.request
from html import unescape
from urllib.parse import urljoin

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
MAX_BYTES = 5 * 1024 * 1024
MAGIC = {b"\xff\xd8\xff": ".jpg", b"\x89PNG": ".png", b"GIF8": ".gif", b"RIFF": ".webp"}


def fetch(url, limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.geturl(), r.read(limit) if limit else r.read()


def check(urls):
    out = []
    for u in urls:
        try:
            status, final, _ = fetch(u, limit=1024)
            out.append({"url": u, "status": status, "final": final, "ok": True})
        except urllib.error.HTTPError as e:
            kind = "blocked" if e.code in (401, 403, 429) else "dead"
            out.append({"url": u, "status": e.code, "ok": False, "kind": kind})
        except Exception as e:
            out.append({"url": u, "ok": False, "kind": "error", "error": str(e)})
    print(json.dumps(out, ensure_ascii=False, indent=1))


def image(page_url, out_base):
    _, final, html = fetch(page_url, limit=600_000)
    html = html.decode("utf-8", "ignore")
    m = None
    for prop in ("og:image", "twitter:image", "og:image:url"):
        m = re.search(rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)', html, re.I) \
            or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{prop}["\']', html, re.I)
        if m:
            break
    if not m:
        print(json.dumps({"page": page_url, "image": None, "reason": "no og:image"}))
        return
    img_url = urljoin(final, unescape(m.group(1)))
    try:
        _, _, data = fetch(img_url, limit=MAX_BYTES + 1)
    except Exception as e:
        print(json.dumps({"page": page_url, "image_url": img_url, "saved": None, "reason": str(e)}))
        return
    if len(data) > MAX_BYTES:
        print(json.dumps({"page": page_url, "image_url": img_url, "saved": None, "reason": "over 5MB"}))
        return
    ext = next((e for sig, e in MAGIC.items() if data.startswith(sig)), None)
    if not ext:
        print(json.dumps({"page": page_url, "image_url": img_url, "saved": None, "reason": "not an image"}))
        return
    path = out_base + ext
    with open(path, "wb") as f:
        f.write(data)
    print(json.dumps({"page": page_url, "image_url": img_url, "saved": path, "bytes": len(data)}))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        check(sys.argv[2:])
    elif len(sys.argv) == 4 and sys.argv[1] == "image":
        image(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(2)
