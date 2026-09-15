#!/usr/bin/env python3
"""Strip every comment from a single-file HTML deck, for the build that goes to a client.

    python3 strip_comments.py <in.html> [out.html]     # write the stripped build
    python3 strip_comments.py <in.html> --check        # report only, write nothing

The working file keeps its comments: they are the record of why the deck draws what it draws. The
client build is a copy with the engineering notes removed and nothing else changed.

WHY A STATE MACHINE AND NOT A REGEX. A deck is full of things that look like comments and are not:
base64 data URIs ("data:image/jpeg;base64,/9j/4AAQ..."), CDN and tile URLs inside strings, and regex
literals such as /Caf|QSR|Restaurant/i. A regex sweep eats those and corrupts the payload silently.
This scanner tracks strings, template literals (including nested ${ }), and the regex-versus-division
ambiguity by the previous significant token.

It asserts two invariants rather than trusting itself:
  1. every removed span begins with //, /* or <!--, and block comments are terminated;
  2. the output is exactly the input minus the recorded spans (a length identity).

HOW TO PROVE A BUILD, once stripped (none of these is optional on a file you are about to send):
  - node --check every inline <script> block (scripts/verify.py does this);
  - walk every beat in a browser and confirm no console error (scripts/frameprobe.mjs --walk);
  - diff the client-visible text of both builds: dump per-section innerText plus every bound value
    from each file and compare. Identical text is the claim you are actually making;
  - run this script again on the output: a second pass must remove zero. That is what proves nothing
    survives mid-line.

js_comment_spans() is imported by verify.py so the structural checks can ignore comment content.
"""

import re
import sys
from pathlib import Path

# A regex literal may begin where an expression may begin. After an identifier, a number or a closing
# bracket, the same slash is division. This is the standard heuristic and it is why the scanner keeps
# the previous significant token.
REGEX_OK_BEFORE = set("([{,;:!&|?+-*/%~^=<>") | {
    "return", "typeof", "instanceof", "in", "of", "new", "delete", "void", "throw",
    "case", "do", "else", "yield", "await",
}

BLOB_ASSIGN = re.compile(r"\s*window\.__\w+__\s*=\s*")


def js_comment_spans(s, base=0):
    """(start, end) of every comment in JS source `s`, offset by `base`."""
    out = []
    i, n = 0, len(s)
    prev = ""
    while i < n:
        c = s[i]
        if c in "\"'":
            q, i = c, i + 1
            while i < n:
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == q:
                    i += 1
                    break
                i += 1
            prev = "str"
            continue
        if c == "`":
            i += 1
            while i < n:
                if s[i] == "\\":
                    i += 2
                    continue
                if s[i] == "`":
                    i += 1
                    break
                if s[i] == "$" and i + 1 < n and s[i + 1] == "{":
                    depth, j = 1, i + 2
                    start = j
                    while j < n and depth:
                        if s[j] == "{":
                            depth += 1
                        elif s[j] == "}":
                            depth -= 1
                        elif s[j] in "\"'`":
                            q = s[j]
                            j += 1
                            while j < n and s[j] != q:
                                j += 2 if s[j] == "\\" else 1
                        j += 1
                    out.extend(js_comment_spans(s[start:j - 1], base + start))
                    i = j
                    continue
                i += 1
            prev = "str"
            continue
        if c == "/" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == "/":
                j = s.find("\n", i)
                j = n if j < 0 else j
                out.append((base + i, base + j))
                i = j
                continue
            if nxt == "*":
                j = s.find("*/", i + 2)
                j = n if j < 0 else j + 2
                out.append((base + i, base + j))
                i = j
                continue
            if prev in REGEX_OK_BEFORE:                    # regex literal, not division
                j, in_class, closed = i + 1, False, False
                while j < n:
                    if s[j] == "\\":
                        j += 2
                        continue
                    if s[j] == "\n":
                        break
                    if s[j] == "[":
                        in_class = True
                    elif s[j] == "]":
                        in_class = False
                    elif s[j] == "/" and not in_class:
                        closed, j = True, j + 1
                        break
                    j += 1
                if closed:
                    while j < n and s[j].isalpha():        # flags
                        j += 1
                    i, prev = j, "re"
                    continue
            prev, i = "/", i + 1
            continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (s[j].isalnum() or s[j] in "_$"):
                j += 1
            prev, i = s[i:j], j
            continue
        if not c.isspace():
            prev = c
        i += 1
    return out


def comment_spans(html):
    """(start, end) of every comment in a whole HTML document: JS, CSS and HTML."""
    spans = []

    for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>", html, re.I):
        a = m.end()
        b = html.find("</script>", a)
        if b < 0:
            continue
        body = html[a:b]
        # a one-line payload assignment is minified JSON: no comments in it, and no reason to push
        # megabytes of base64 through the scanner
        if BLOB_ASSIGN.match(body) and "\n" not in body.strip():
            continue
        spans.extend(js_comment_spans(body, a))

    for m in re.finditer(r"<style[^>]*>", html, re.I):
        a = m.end()
        b = html.find("</style>", a)
        if b < 0:
            continue
        for cm in re.finditer(r"/\*.*?\*/", html[a:b], re.S):
            spans.append((a + cm.start(), a + cm.end()))

    blocked = []
    for tag in ("script", "style"):
        for m in re.finditer(r"<%s[^>]*>" % tag, html, re.I):
            b = html.find("</%s>" % tag, m.end())
            blocked.append((m.start(), b if b > 0 else len(html)))
    for m in re.finditer(r"<!--.*?-->", html, re.S):
        if not any(s <= m.start() < e for s, e in blocked):
            spans.append((m.start(), m.end()))

    spans.sort()
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        assert e1 <= s2, "overlapping comment spans at %d and %d" % (s1, s2)
    for s, e in spans:
        frag = html[s:e]
        assert frag.startswith(("//", "/*", "<!--")), "not a comment at %d: %r" % (s, frag[:60])
        if frag.startswith("/*"):
            assert frag.endswith("*/"), "unterminated block comment at %d" % s
        if frag.startswith("<!--"):
            assert frag.endswith("-->"), "unterminated html comment at %d" % s
    return spans


def strip(html):
    spans = comment_spans(html)
    out, prev = [], 0
    for s, e in spans:
        out.append(html[prev:s])
        prev = e
    out.append(html[prev:])
    txt = "".join(out)
    assert len(txt) == len(html) - sum(e - s for s, e in spans), "span accounting does not balance"

    lines, keep = txt.split("\n"), []            # drop lines a comment emptied, collapse blank runs
    for i, l in enumerate(lines):
        r = l.rstrip()
        if r == "" and i and lines[i - 1].rstrip() == "":
            continue
        keep.append(r)
    return "\n".join(keep), spans


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    if not args:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    src = Path(args[0])
    html = src.read_text(encoding="utf-8")
    txt, spans = strip(html)

    kind = lambda p: "html" if html[p[0]:p[1]].startswith("<!--") else ("block" if html[p[0]:p[1]].startswith("/*") else "line")
    counts = {"line": 0, "block": 0, "html": 0}
    for p in spans:
        counts[kind(p)] += 1
    print("comments removed : %d  (line %d, block %d, html %d)"
          % (len(spans), counts["line"], counts["block"], counts["html"]))
    print("characters       : %d -> %d" % (len(html), len(txt)))

    if check:
        return 0
    dst = Path(args[1]) if len(args) > 1 else src
    dst.write_text(txt, encoding="utf-8")
    left = len(comment_spans(txt))               # idempotence: a second pass must find nothing
    print("written          : %s" % dst)
    print("second pass      : %d comment(s) left%s" % (left, "" if left == 0 else "  <-- INVESTIGATE"))
    return 0 if left == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
