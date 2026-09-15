#!/usr/bin/env python3
"""No-browser verification for a single-file HTML deck.

Runs the checks that catch mechanical failure, in order: syntax -> banned tokens -> structure/dispatch
-> lints. Hard failures exit non-zero; heuristic concerns warn without failing.

Usage:
  python3 verify.py <deck.html> [--ban "str1,str2"] [--simulate builder.js]

This is the STATIC half of verification. The dynamic half is scripts/frameprobe.mjs, which measures
frame behaviour, stalls and console errors in a real browser. Neither replaces the other, and neither
judges whether the deck looks right.

Structural checks run on a COMMENT-STRIPPED copy (via strip_comments.js_comment_spans). Comments are
not inert here: a <section> written inside a JS comment inflates the section count, and a beat named
only in comments reads as wired when it is not. Both were observed on a real deck.

The optional --simulate hook runs a project-supplied node script (which should load the deck's data blob
and assert its builders produce non-empty output); this is the deck-specific step the generic checks
cannot cover. See ../references/html_surgery.md.
"""

import re
import sys
import argparse
import subprocess
import tempfile
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_comments import comment_spans                            # noqa: E402

EM_DASH = "—"
TAG = re.compile(r"<[^>]+>")
SECTION_STEP = re.compile(r"<section\b[^>]*?data-step\s*=\s*[\"']([^\"']+)[\"']", re.I)
INLINE_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)


def has_node():
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def check_syntax(html):
    """node --check every inline JS <script> block. type=application/json and external src are skipped."""
    fails = []
    n_checked = 0
    for m in INLINE_SCRIPT.finditer(html):
        attrs, body = m.group(1), m.group(2)
        if "src=" in attrs.lower():
            continue
        tm = re.search(r"type\s*=\s*[\"']([^\"']+)[\"']", attrs, re.I)
        if tm and tm.group(1).lower() not in ("text/javascript", "module", "application/javascript"):
            continue                      # e.g. application/json data blob, not JS
        if not body.strip():
            continue
        n_checked += 1
        line = html[:m.start()].count("\n") + 1
        with tempfile.NamedTemporaryFile("w", suffix=".mjs" if (tm and tm.group(1).lower() == "module") else ".js",
                                         delete=False, encoding="utf-8") as tf:
            tf.write(body)
            tmp = tf.name
        try:
            r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
            if r.returncode != 0:
                err = (r.stderr.strip().splitlines() or ["syntax error"])[0]
                fails.append("script block near line %d: %s" % (line, err))
        finally:
            os.unlink(tmp)
    return n_checked, fails


def _mask_blocks(html):
    """Blank out every <script>/<style> span (contents AND tags), preserving newlines so line
    numbers stay true. Handles same-line opens and giant one-line data blobs correctly."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    html = re.sub(r"<script\b.*?</script>", blank, html, flags=re.I | re.S)
    html = re.sub(r"<style\b.*?</style>", blank, html, flags=re.I | re.S)
    return html


def blank_comments(html):
    """Replace every comment's characters with spaces, keeping length and newlines so offsets and
    line numbers stay true. Structural checks read this, never the raw file."""
    out = list(html)
    for s, e in comment_spans(html):
        for i in range(s, e):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def check_banned(html, extra):
    """Scan VISIBLE copy (outside <script>/<style>, outside comments) for banned tokens, preserving
    real line numbers. A comment is not visible copy: the house rule bans em dashes on screen, not in
    the notes that explain the code. Data-driven copy inside blobs is not reachable here; known limit."""
    banned = {EM_DASH: "em dash"}
    for s in extra:
        if s:
            banned[s] = "banned token %r" % s
    masked = _mask_blocks(blank_comments(html))
    hits = []
    for i, raw in enumerate(masked.splitlines(), start=1):
        visible = TAG.sub("", raw)
        for tok, label in banned.items():
            if tok in visible:
                hits.append("line %d: %s in visible copy: %r" % (i, label, visible.strip()[:80]))
    return hits


def check_structure(html):
    """Count sections, flag duplicate data-steps (hard), warn on possibly-unwired steps (soft).
    Runs on a comment-blanked copy: a <section> inside a comment is not a section, and a beat id
    mentioned only in prose is not wiring."""
    html = blank_comments(html)
    steps = SECTION_STEP.findall(html)
    n_sections = len(re.findall(r"<section\b", html, re.I))
    dupes, seen = [], set()
    for s in steps:
        if s in seen:
            dupes.append(s)
        seen.add(s)
    unwired = []
    for s in set(steps):
        refs = len(re.findall(r"\b" + re.escape(s) + r"\b", html))
        if refs <= steps.count(s):          # appears only in the section tag(s), nowhere else
            unwired.append(s)
    return n_sections, steps, dupes, unwired


def check_lints(html):
    """Two cheap static lints for failures that cost real time to find dynamically. Warn, never fail:
    both have legitimate small-scale exceptions."""
    warns = []
    clean = blank_comments(html)

    # 1. determinism. The engine seeds every random placement (mulberry32) so frames are reproducible;
    #    a stray Math.random makes a rebuild differ from the frame someone approved.
    for m in re.finditer(r"\bMath\.random\s*\(", clean):
        warns.append("line %d: Math.random() breaks frame determinism; seed with mulberry32"
                     % (clean[:m.start()].count("\n") + 1))

    # 2. the quadratic path. Canvas path building is QUADRATIC in the number of CLOSED subpaths in one
    #    path: at ~1k rings a few ms, at ~20k over a second, per frame. Accumulating many rings into
    #    one path is right; closing them with closePath() is what costs. Close with lineTo(first).
    #    Detected shape: a closePath() inside a loop whose beginPath() sits outside it.
    for m in re.finditer(r"\b(for|while)\s*\(", clean):
        start = clean.find("{", m.end())
        if start < 0 or start - m.end() > 200:
            continue
        depth, i, n = 1, start + 1, len(clean)
        while i < n and depth:
            if clean[i] == "{":
                depth += 1
            elif clean[i] == "}":
                depth -= 1
            i += 1
        body = clean[start:i]
        if len(body) > 4000:
            continue
        if "closePath" in body and "beginPath" not in body:
            warns.append("line %d: closePath() in a loop whose beginPath() is outside it. Path "
                         "building is quadratic in closed subpaths; close rings with lineTo(first). "
                         "See references/performance.md" % (clean[:start].count("\n") + 1))
    return warns


def run_simulate(path):
    r = subprocess.run(["node", path], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    ap = argparse.ArgumentParser(description="No-browser verification for a single-file HTML deck.")
    ap.add_argument("deck")
    ap.add_argument("--ban", default="", help="extra banned tokens, comma-separated")
    ap.add_argument("--simulate", default=None, help="node script that asserts builders render non-empty")
    args = ap.parse_args()

    html = open(args.deck, encoding="utf-8", errors="replace").read()
    hard = 0

    print("== syntax ==")
    if not has_node():
        print("  FAIL: node not found; cannot check inline scripts")
        hard += 1
    else:
        n, fails = check_syntax(html)
        if fails:
            hard += len(fails)
            for f in fails:
                print("  FAIL: " + f)
        else:
            print("  ok: %d inline script block(s) pass node --check" % n)

    print("== banned tokens ==")
    hits = check_banned(html, args.ban.split(","))
    if hits:
        hard += len(hits)
        for h in hits:
            print("  FAIL: " + h)
    else:
        print("  ok: no banned tokens in visible copy")

    print("== structure ==")
    n_sections, steps, dupes, unwired = check_structure(html)
    print("  %d <section> tag(s), %d with data-step" % (n_sections, len(steps)))
    if dupes:
        hard += len(dupes)
        for d in sorted(set(dupes)):
            print("  FAIL: duplicate data-step %r" % d)
    if unwired:
        for u in sorted(unwired):
            print("  warn: data-step %r referenced only in its section tag (possibly unwired)" % u)
    if not dupes and not unwired:
        print("  ok: no duplicate or unwired data-steps")

    print("== lints ==")
    warns = check_lints(html)
    if warns:
        for w in warns:
            print("  warn: " + w)
    else:
        print("  ok: no determinism or quadratic-path lint")

    if args.simulate:
        print("== simulate ==")
        rc, out = run_simulate(args.simulate)
        print(("  ok: " if rc == 0 else "  FAIL: ") + (out or "(no output)"))
        if rc != 0:
            hard += 1

    print("\n%s (%d hard failure%s)" % ("PASS" if hard == 0 else "FAIL", hard, "" if hard == 1 else "s"))
    print("static only. Run scripts/frameprobe.mjs for frame behaviour, then have a person open it.")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
