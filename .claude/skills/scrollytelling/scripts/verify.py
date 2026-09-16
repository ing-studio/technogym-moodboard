#!/usr/bin/env python
"""Static verification for the gym scroll deck. No browser; seconds. Run after every edit.

  python verify.py deck/index.html [--ban "str1,str2"] [--unused]

Hard failures (exit 1):
  syntax     every inline JS <script> passes `node --check`
  data       __DATA__ markers present once, blob parses, every image src exists, every image has alt
  copy       no em dash in visible copy, PHASES strings (tags, labels) or inlined titles/alt/fact
             displays; no --ban tokens
  structure  no duplicate data-step; every data-step has a PHASES entry and a data-chapter;
             every PHASES layer is none, figure or grid
  refs       every image id named in the engine exists in __DATA__.images; every frame group and
             focus id exists in __DATA__.annotations (story/annotations.json)
  imgs       every static <img> has non-empty alt and (if it has a src) an existing file
  binds      every data-bind id exists in __DATA__.facts
  offline    no fetch( or XMLHttpRequest: the deck must work by double-click (file://)
  board      story/storyboard.md lists the same step ids in the same order as the deck. The
             storyboard is the agreed running order, so drift between the two is a failure
Warnings: PHASES entries with no section, assumed facts with no source, a grid whose tile count
leaves an orphan in the last row, an image shown in more than one beat, a skill kit that no longer
matches the deck (scripts/sync_kit.py). --unused lists catalogued images no beat shows, which is
the list to choose from when a beat needs more pictures.

This is the static half. scripts/shotbeat.mjs photographs a beat in a real browser; a person judges the rest.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EM_DASH = "\u2014"
START, END = "/*__DATA__*/", "/*__END__*/"
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
SECTION_STEP = re.compile(r"<section\b[^>]*?data-step\s*=\s*[\"']([^\"']+)[\"']", re.I)
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
IMAGE_ID = re.compile(r"[\"']((?:vision|mood)-\d{2}(?:-[a-z0-9]+)+|plan-level-[a-z0-9]+)[\"']")
PHASES_BLOCK = re.compile(r"var\s+PHASES\s*=\s*\{(.*?)\n\s*\};", re.S)
LAYERS = ("none", "figure", "grid")
STEP_TAG = re.compile(r"<section\b[^>]*?data-step\s*=[^>]*>", re.I)
PHASE_KEY = re.compile(r"(?m)^\s*[\"']?([A-Za-z0-9_-]+)[\"']?\s*:\s*\{")
BOARD_ROW = re.compile(r"(?m)^\|\s*\d+\s*\|\s*([A-Za-z0-9_-]+)\s*\|")
SPEC_IMAGE = re.compile(r"\bimage\s*:\s*[\"']([^\"']+)[\"']")
TILE = re.compile(r"\{[^{}]*\b(?:image|text)\s*:")


def attr(tag, name):
    m = re.search(r"\b" + name + r"\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return None if m is None else m.group(2)


def find_node():
    n = shutil.which("node")
    if n:
        return n
    for p in (r"C:\Program Files\nodejs\node.exe", os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\node.exe")):
        if os.path.isfile(p):
            return p
    return None


def blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def visible_html(html):
    """HTML with scripts, styles and comments blanked (newlines kept, so line numbers stay true)."""
    html = re.sub(r"<!--.*?-->", blank, html, flags=re.S)
    html = re.sub(r"<script\b.*?</script>", blank, html, flags=re.I | re.S)
    return re.sub(r"<style\b.*?</style>", blank, html, flags=re.I | re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--ban", default="")
    ap.add_argument("--unused", action="store_true", help="list catalogued images no beat shows")
    a = ap.parse_args()

    html = open(a.deck, encoding="utf-8").read()
    base = os.path.dirname(os.path.abspath(a.deck))
    fails, warns = [], []

    # syntax
    node = find_node()
    scripts = [(m.group(1), m.group(2), m.start()) for m in INLINE_SCRIPT.finditer(html)]
    if not node:
        fails.append("syntax: node not found; install Node LTS")
    else:
        for attrs, body, pos in scripts:
            if "src=" in attrs.lower() or not body.strip():
                continue
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
                tf.write(body)
            r = subprocess.run([node, "--check", tf.name], capture_output=True, text=True)
            os.unlink(tf.name)
            if r.returncode:
                err = (r.stderr.strip().splitlines() or ["syntax error"])[-1]
                fails.append("syntax: script near line %d: %s" % (html.count("\n", 0, pos) + 1, err))

    # data blob
    blobs = re.findall(re.escape(START) + r"(.*?)" + re.escape(END), html, re.S)
    data = {"images": {}, "annotations": {}, "facts": {}}
    if len(blobs) != 1:
        fails.append("data: expected __DATA__ markers once, found %d" % len(blobs))
    else:
        try:
            data = json.loads(blobs[0])
        except ValueError as e:
            fails.append("data: blob does not parse: %s" % e)
    images, facts, notes = data.get("images", {}), data.get("facts", {}), data.get("annotations", {})
    if not images:
        fails.append("data: no images inlined; run moodboard-assets/scripts/build_data.py")
    for iid, m in images.items():
        if not os.path.isfile(os.path.join(base, m.get("src", ""))):
            fails.append("data: %s src missing on disk: %s" % (iid, m.get("src")))
        if not str(m.get("alt", "")).strip():
            fails.append("data: %s has no alt text" % iid)
        for k in ("title", "alt"):
            if EM_DASH in str(m.get(k, "")):
                fails.append("copy: em dash in %s of %s" % (k, iid))
    for fid, f in facts.items():
        if EM_DASH in str(f.get("display", "")):
            fails.append("copy: em dash in display of fact %s" % fid)
        if f.get("assumed") and not f.get("source"):
            warns.append("fact %s is assumed but has no source note" % fid)

    # visible copy
    vis = visible_html(html)
    bans = {EM_DASH: "em dash"}
    bans.update({t: "banned token %r" % t for t in a.ban.split(",") if t})
    for i, line in enumerate(vis.splitlines(), 1):
        text = re.sub(r"<[^>]+>", "", line)
        for tok, label in bans.items():
            if tok in text:
                fails.append("copy: line %d: %s: %r" % (i, label, text.strip()[:80]))

    # structure
    steps = SECTION_STEP.findall(vis)
    dupes = sorted({s for s in steps if steps.count(s) > 1})
    fails += ["structure: duplicate data-step %r" % d for d in dupes]
    engine = "\n".join(body for attrs, body, _ in scripts if START not in body)
    pm = PHASES_BLOCK.search(engine)
    keys = PHASE_KEY.findall(pm.group(1)) if pm else []
    if not pm:
        fails.append("structure: no `var PHASES = {...};` block found")
    fails += ["structure: data-step %r has no PHASES entry (beat renders nothing)" % s for s in steps if s not in keys]
    warns += ["PHASES entry %r has no section" % k for k in keys if k not in steps]
    for m in STEP_TAG.finditer(vis):
        if not (attr(m.group(0), "data-chapter") or "").strip():
            fails.append("structure: section %r has no data-chapter" % attr(m.group(0), "data-step"))
    body = pm.group(1) if pm else ""
    if EM_DASH in body:
        fails.append("copy: em dash in a PHASES string (tag or label)")
    for lay in re.findall(r"\blayer\s*:\s*[\"']([^\"']+)[\"']", body):
        if lay not in LAYERS:
            fails.append("structure: unknown layer %r (use %s)" % (lay, ", ".join(LAYERS)))
    for obj in re.findall(r"\{[^{}]*\bgroup\s*:[^{}]*\}", body):
        im = re.search(r"\bimage\s*:\s*[\"']([^\"']+)", obj)
        grp = re.search(r"\bgroup\s*:\s*[\"']([^\"']+)", obj).group(1)
        if im and not any(a.get("group") == grp for a in notes.get(im.group(1), [])):
            fails.append("refs: frame %s has group %r with no boxes in story/annotations.json" % (im.group(1), grp))
    ids = {a.get("id") for lst in notes.values() for a in lst}
    for fid in re.findall(r"\bfocus\s*:\s*[\"']([^\"']+)[\"']", body):
        if fid not in ids:
            fails.append("refs: focus %r is not a box id in story/annotations.json" % fid)

    # storyboard parity: the running order is agreed on paper, so the deck must match it
    board = os.path.join(os.path.dirname(base), "story", "storyboard.md")
    if os.path.isfile(board):
        rows = BOARD_ROW.findall(open(board, encoding="utf-8").read())
        if rows:
            fails += ["board: beat %r is in the deck but not in story/storyboard.md" % s
                      for s in steps if s not in rows]
            fails += ["board: story/storyboard.md lists %r, which is not a beat in the deck" % s
                      for s in rows if s not in steps]
            shared = [s for s in steps if s in rows]
            if [s for s in rows if s in steps] != shared:
                fails.append("board: storyboard order (%s) does not match the deck (%s)"
                             % (" ".join(s for s in rows if s in steps), " ".join(shared)))

    # per-beat specs: grid shape, and the same picture shown twice
    starts = [(m.group(1), m.start()) for m in PHASE_KEY.finditer(body)]
    used = {}
    for i, (key, pos) in enumerate(starts):
        spec = body[pos:starts[i + 1][1] if i + 1 < len(starts) else len(body)]
        for iid in SPEC_IMAGE.findall(spec):
            used.setdefault(iid, []).append(key)
        if re.search(r"layer\s*:\s*[\"']grid[\"']", spec):
            cm = re.search(r"\bcols\s*:\s*(\d+)", spec)
            cols = int(cm.group(1)) if cm else 3
            n = len(TILE.findall(spec))
            wide = re.search(r"size\s*:\s*[\"'](?:big|wide)[\"']", spec)
            if cols > 1 and not wide and n > cols and n % cols == 1:
                warns.append("grid %r: %d tiles in %d columns leaves an orphan in the last row" % (key, n, cols))
    repeats = ["%s (%s)" % (i, ", ".join(w)) for i, w in sorted(used.items()) if len(w) > 1]
    if repeats:   # deliberate in the vision chapter, usually an oversight in the mood chapter
        warns.append("shown in more than one beat: " + "; ".join(repeats))

    # kit freshness: references/ must still match the deck
    sync = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_kit.py")
    if os.path.isfile(sync):
        r = subprocess.run([sys.executable, sync, a.deck, "--check"], capture_output=True, text=True)
        if r.returncode:
            warns.append(r.stdout.strip().replace("FAIL: ", "") or "skill kit is stale; run sync_kit.py")

    # image refs in the engine
    for iid in sorted(set(IMAGE_ID.findall(engine))):
        if images and iid not in images:
            fails.append("refs: engine names image %r, not in __DATA__.images" % iid)

    # static imgs
    for m in IMG_TAG.finditer(vis):
        tag, line = m.group(0), vis.count("\n", 0, m.start()) + 1
        alt, src = attr(tag, "alt"), attr(tag, "src")
        if not (alt or "").strip():
            fails.append("imgs: line %d: <img> without alt text" % line)
        if src and not src.startswith(("data:", "http")) and not os.path.isfile(os.path.join(base, src)):
            fails.append("imgs: line %d: src not found: %s" % (line, src))

    # binds
    for bid in sorted(set(re.findall(r"data-bind\s*=\s*[\"']([^\"']+)[\"']", vis))):
        if bid not in facts:
            fails.append("binds: data-bind %r has no entry in story/facts.json" % bid)

    # offline
    for pat in (r"\bfetch\s*\(", r"XMLHttpRequest"):
        if re.search(pat, engine):
            fails.append("offline: %s used; inline data with build_data.py instead" % pat)

    print("deck: %s  (%d sections, %d PHASES, %d images, %d facts)" % (a.deck, len(steps), len(keys), len(images), len(facts)))
    if a.unused:
        shown = set(IMAGE_ID.findall(engine))
        idle = [i for i in sorted(images) if i not in shown]
        print("  unused (%d of %d catalogued): %s" % (len(idle), len(images), ", ".join(idle) or "none"))
    for w in warns:
        print("  warn: " + w)
    for f in fails:
        print("  FAIL: " + f)
    print("%s (%d hard failure%s)" % ("PASS" if not fails else "FAIL", len(fails), "" if len(fails) == 1 else "s"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
