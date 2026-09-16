#!/usr/bin/env python
"""Bundle the deck into one portable HTML file: every picture inlined, nothing to ship beside it.

  python build_standalone.py [deck/index.html] [-o fitness-moodboard.html]

The deck in deck/ points at ../assets/web/*.webp, so it only runs inside the project. This writes a copy
whose images are data: URIs, for sending to a client or opening from a memory stick. It is a build output,
never edited by hand: change deck/index.html and run this again.

Images the deck never shows are dropped from the blob (verify.py --unused lists them), so the file carries
what it needs and no more. Everything else, including the engine and the design system, is already inline.
"""

import argparse
import base64
import json
import os
import re
import sys

START, END = "/*__DATA__*/", "/*__END__*/"
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
IMAGE_ID = re.compile(r"[\"']((?:vision|mood)-\d{2}(?:-[a-z0-9]+)+|plan-level-[a-z0-9]+)[\"']")
IMG_SRC = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*([\"']))(.*?)(\2)", re.I | re.S)
MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".gif": "image/gif"}


def data_uri(path):
    mime = MIME.get(os.path.splitext(path)[1].lower())
    if not mime:
        sys.exit("no mime type known for %s" % path)
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode("ascii"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", nargs="?", default="deck/index.html")
    ap.add_argument("-o", "--out", default="fitness-moodboard.html")
    a = ap.parse_args()

    html = open(a.deck, encoding="utf-8").read()
    base = os.path.dirname(os.path.abspath(a.deck))

    m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), html, re.S)
    if not m:
        sys.exit("no __DATA__ blob in %s" % a.deck)
    data = json.loads(m.group(1))

    engine = "\n".join(b for attrs, b, in ((x.group(1), x.group(2)) for x in INLINE_SCRIPT.finditer(html))
                       if START not in b)
    shown = set(IMAGE_ID.findall(engine))
    kept, dropped, total = {}, [], 0
    for iid, meta in data.get("images", {}).items():
        if iid not in shown:
            dropped.append(iid)
            continue
        path = os.path.join(base, meta["src"])
        if not os.path.isfile(path):
            sys.exit("missing image on disk: %s (run make_web.py)" % path)
        total += os.path.getsize(path)
        kept[iid] = dict(meta, src=data_uri(path))
    data["images"] = kept
    html = html[:m.start()] + START + json.dumps(data, ensure_ascii=False) + END + html[m.end():]

    # static images in the markup (the studio logo)
    files = set()

    def swap(mo):
        src = mo.group(3)
        if src.startswith(("data:", "http")):
            return mo.group(0)
        path = os.path.join(base, src)
        if not os.path.isfile(path):
            sys.exit("missing file on disk: %s" % path)
        files.add(os.path.normpath(path))
        return mo.group(1) + data_uri(path) + mo.group(4)

    html = IMG_SRC.sub(swap, html)
    total += sum(os.path.getsize(p) for p in files)

    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(html)
    print("ok: %s  %.1f MB  (%d images inlined from %.1f MB, %d unused dropped)"
          % (a.out, os.path.getsize(a.out) / 1e6, len(kept) + len(files), total / 1e6, len(dropped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
