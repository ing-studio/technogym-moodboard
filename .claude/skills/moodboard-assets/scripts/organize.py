#!/usr/bin/env python
"""Rename and move source images into assets/source/<chapter>/, provably without loss.

Two steps, so a person can read the plan before anything moves:
  python organize.py --plan    # validate assets/rename-map.json, write assets/rename-log.csv
  python organize.py --apply   # move per the log, re-hash every destination, seed catalog.json

Run from the project root. Moves are done in Python with explicit paths, never shell globs: the
original folder had files named "-1.jpg" (read as a command option) and a folder with a space in it.

--apply fails (and stops) if a destination already exists, if a hash differs after the move, or if
any source is still present. The log keeps old path, new path and sha256 so the move can be reversed.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys

MAP = "assets/rename-map.json"
LOG = "assets/rename-log.csv"
CATALOG = "assets/catalog.json"
SRC = "assets/source"
NAME = re.compile(r"^(vision|plan|mood)-[a-z0-9]+(-[a-z0-9]+)*\.(jpg|png)$")
CHAPTERS = {"01-vision": "vision", "02-floor-plan": "plan", "03-mood": "mood"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dest(it):
    return "%s/%s/%s" % (SRC, it["chapter"], it["new"])


def done(it):
    """Already organized in an earlier run: source gone, destination present."""
    return not os.path.exists(it["old"]) and os.path.isfile(dest(it))


def plan():
    items = json.load(open(MAP, encoding="utf-8"))["images"]
    history = {}
    if os.path.exists(LOG):
        history = {r["new"]: r for r in csv.DictReader(open(LOG, encoding="utf-8"))}
    errors, seen = [], set()
    for it in items:
        old, new, ch = it["old"], it["new"], it["chapter"]
        if done(it):
            seen.add(new)
            continue
        if not os.path.isfile(old):
            errors.append("missing source: %s" % old)
        if ch not in CHAPTERS:
            errors.append("unknown chapter %r for %s" % (ch, old))
        elif not new.startswith(CHAPTERS[ch] + "-"):
            errors.append("%s does not match chapter %s" % (new, ch))
        if not NAME.match(new):
            errors.append("bad name: %s" % new)
        if new in seen:
            errors.append("duplicate new name: %s" % new)
        seen.add(new)
        for k in ("title", "alt"):
            if not it.get(k, "").strip():
                errors.append("empty %s for %s" % (k, old))
    if errors:
        print("\n".join("FAIL: " + e for e in errors))
        return 1
    pending = 0
    with open(LOG, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["old", "new", "sha256"])
        for it in items:
            if done(it):
                prev = history.get(dest(it))
                w.writerow([it["old"], dest(it), prev["sha256"] if prev else sha(dest(it))])
            else:
                w.writerow([it["old"], dest(it), sha(it["old"])])
                pending += 1
    print("ok: %d images to move (%d already organized), log written to %s" % (pending, len(items) - pending, LOG))
    return 0


def apply():
    rows = [r for r in csv.DictReader(open(LOG, encoding="utf-8"))
            if not (not os.path.exists(r["old"]) and os.path.isfile(r["new"]))]
    if not rows:
        print("ok: nothing to move")
        return 0
    for r in rows:
        if os.path.exists(r["new"]):
            print("FAIL: destination exists, refusing to overwrite: " + r["new"])
            return 1
        if not os.path.isfile(r["old"]) or sha(r["old"]) != r["sha256"]:
            print("FAIL: source missing or changed since --plan: " + r["old"])
            return 1
    for r in rows:
        os.makedirs(os.path.dirname(r["new"]), exist_ok=True)
        shutil.move(r["old"], r["new"])
    bad = [r["new"] for r in rows if not os.path.isfile(r["new"]) or sha(r["new"]) != r["sha256"]]
    left = [r["old"] for r in rows if os.path.exists(r["old"])]
    if bad or left:
        print("FAIL: hash mismatch %s; sources left %s" % (bad, left))
        return 1

    # seed catalog.json with the hand-written fields; catalog.py fills in the measured ones
    items = {it["new"]: it for it in json.load(open(MAP, encoding="utf-8"))["images"]}
    cat = json.load(open(CATALOG, encoding="utf-8")) if os.path.exists(CATALOG) else {"images": []}
    known = {e["id"] for e in cat["images"]}
    for r in rows:
        it = items[os.path.basename(r["new"])]
        iid = os.path.splitext(it["new"])[0]
        if iid not in known:
            cat["images"].append({"id": iid, "file": r["new"], "chapter": it["chapter"],
                                  "title": it["title"], "alt": it["alt"], "tags": it["tags"],
                                  "sha256": r["sha256"], "original": r["old"]})
    with open(CATALOG, "w", encoding="utf-8") as fh:
        json.dump(cat, fh, indent=2, ensure_ascii=False)
    print("ok: %d images moved and verified; catalog seeded" % len(rows))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.exit(plan() if a.plan else apply())
