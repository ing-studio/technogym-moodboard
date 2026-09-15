#!/usr/bin/env python
"""Inline the deck's data into deck/index.html so it works by double-click (file://, no fetch).

  python build_data.py [--deck deck/index.html]

Reads assets/catalog.json, story/areas.json and story/facts.json, writes one `window.__DATA__` object
between the markers

  /*__DATA__*/ ... /*__END__*/

Parse -> replace -> write last: if the markers are not found exactly once, nothing is written.
Image paths are rewritten relative to the deck file. Only fields the deck uses are inlined.
"""

import argparse
import json
import os
import re
import sys

START, END = "/*__DATA__*/", "/*__END__*/"
KEEP = ("id", "chapter", "title", "alt", "tags", "palette", "web_w", "web_h", "orientation")


def load(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="deck/index.html")
    a = ap.parse_args()

    cat = load("assets/catalog.json", {"images": []})
    deck_dir = os.path.dirname(os.path.abspath(a.deck))
    images = {}
    missing_web = []
    for e in cat["images"]:
        if "web" not in e:
            missing_web.append(e["id"])
            continue
        item = {k: e[k] for k in KEEP if k in e}
        item["src"] = os.path.relpath(os.path.abspath(e["web"]), deck_dir).replace("\\", "/")
        images[e["id"]] = item
    if missing_web:
        print("FAIL: no web derivative for %s; run make_web.py first" % missing_web)
        return 1

    data = {
        "images": images,
        "areas": load("story/areas.json", {"levels": {}})["levels"],
        "facts": load("story/facts.json", {"facts": {}})["facts"],
    }

    html = open(a.deck, encoding="utf-8").read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    found = pattern.findall(html)
    if len(found) != 1:
        print("FAIL: expected the __DATA__ markers exactly once in %s, found %d" % (a.deck, len(found)))
        return 1
    blob = START + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + END
    html = pattern.sub(lambda m: blob, html, count=1)
    with open(a.deck, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print("ok: inlined %d images, %d plan levels, %d facts (%.0f KB blob)"
          % (len(images), len(data["areas"]), len(data["facts"]), len(blob) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
