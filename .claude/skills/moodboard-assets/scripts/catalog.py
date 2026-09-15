#!/usr/bin/env python
"""Measure every image under assets/source/ into assets/catalog.json, keeping hand-written fields.

  python catalog.py [--check]

Measured fields (w, h, bytes, orientation, palette, sha256, chapter, file) are rewritten on every run.
Hand-written fields (title, alt, tags, and anything else not measured) are kept, matched by id (the
file name without extension). A new file gets empty title/alt so the gap is visible, never invented.
Entries whose file no longer exists are dropped and reported.

--check exits non-zero if any entry has an empty title or alt; run it before building the deck.
"""

import argparse
import hashlib
import json
import os
import sys

from PIL import Image, ImageOps

SRC = "assets/source"
CATALOG = "assets/catalog.json"
MEASURED = ("file", "chapter", "w", "h", "bytes", "orientation", "palette", "sha256")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def palette(im, n=5):
    """Dominant colours, most frequent first, as hex. Quantised from a small thumbnail."""
    small = im.convert("RGB")
    small.thumbnail((96, 96))
    q = small.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    return ["#%02x%02x%02x" % tuple(pal[i * 3:i * 3 + 3]) for _, i in counts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    old = {}
    if os.path.exists(CATALOG):
        old = {e["id"]: e for e in json.load(open(CATALOG, encoding="utf-8"))["images"]}

    out = []
    for chapter in sorted(os.listdir(SRC)):
        d = os.path.join(SRC, chapter)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name).replace("\\", "/")
            iid = os.path.splitext(name)[0]
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im)
                w, h = im.size
                pal = palette(im)
            e = dict(old.get(iid, {"title": "", "alt": "", "tags": []}))
            e.update({"id": iid, "file": p, "chapter": chapter, "w": w, "h": h,
                      "bytes": os.path.getsize(p),
                      "orientation": "landscape" if w > h * 1.1 else "portrait" if h > w * 1.1 else "square",
                      "palette": pal, "sha256": sha(p)})
            out.append({"id": e.pop("id"), **e})

    dropped = sorted(set(old) - {e["id"] for e in out})
    with open(CATALOG, "w", encoding="utf-8") as fh:
        json.dump({"images": out}, fh, indent=2, ensure_ascii=False)
    by_ch = {}
    for e in out:
        by_ch[e["chapter"]] = by_ch.get(e["chapter"], 0) + 1
    print("ok: %d images %s" % (len(out), by_ch))
    if dropped:
        print("warn: dropped entries with no file: %s" % dropped)

    missing = [e["id"] for e in out if not e.get("title", "").strip() or not e.get("alt", "").strip()]
    if missing:
        print(("FAIL" if a.check else "warn") + ": empty title/alt: %s" % missing)
        if a.check:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
