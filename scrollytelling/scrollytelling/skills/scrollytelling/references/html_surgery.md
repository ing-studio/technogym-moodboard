# HTML surgery

Change a big single-file HTML deck precisely, and prove it still works from the terminal before a human
opens it. The target is a self-contained file too large to read top to bottom: inline data blobs, several
inline scripts, thousands of lines. A browser check is the last step, not the loop.

## When this applies

- One HTML file, hundreds of KB or more, with data and logic inlined.
- A targeted change (a number, a label, a beat, a section move) that must not break the rest by accident.
- You cannot render it in this environment, so correctness comes from static plus simulated checks.

## Editing giant data blobs

Big data lives in one enormous single line (a minified JSON-ish assignment). Do not edit it by line number
and do not hand-edit it.

- Locate the blob by a stable **prefix** (the assignment target, e.g. a `window.__DATA__ =` marker), not by
  position. Line numbers drift with every edit.
- **Parse, modify, dump**: read the file, find the blob by prefix, parse it, change the field, serialise it
  back, write the file. Never splice raw text inside a giant line.

## Atomic edit scripts

Make edits with a tiny script, not by hand, so every change is asserted and reversible-by-abort.

- A helper `rep(old, new, tag)` that asserts `old` occurs **exactly once** before replacing. One assertion
  per anchor. If a target is ambiguous, tighten the anchor rather than reaching for replace-all.
- **Write the file LAST.** Collect every replacement in memory, run every assertion first, and only then
  write. A failed assertion aborts with the original untouched (fail-atomic), so a half-applied edit is
  impossible.

## No-browser verification (the core value)

Run `scripts/verify.py <file>` (or reproduce it) after every change, in order:

1. **Syntax**: `node --check` every inline `<script>` block. Catches the obvious breakage.
2. **Simulate**: extract the inline data blob and run the render/builder logic in node against it. This
   catches the silent failures a syntax check cannot: empty output, a missing key, a duplicate key that
   shadows another (still valid syntax, renders nothing). Reproduce the key builder logic and assert the
   output is non-empty and correct.
3. **Banned tokens**: sweep for anything that must never appear on screen. Em dashes in visible copy at
   minimum; add any string the brief forbids (a figure you must not show, a leftover placeholder).
4. **Structure**: count sections and check dispatch coverage. Anchor the probe on the real opening tag
   (`<section`), not on an attribute selector like `data-step="..."`, which also matches CSS rules and gives
   false counts. Every `data-step` in the HTML must have a matching scene spec, and every scene flag a spec
   sets must be honoured in the draw path.

Then `scripts/frameprobe.mjs` measures what the static checks cannot: frame behaviour, stalls, console
errors, per-beat card reveal. See `performance.md`. Only after both does a human open it, for the things
neither can judge: whether the composition works, whether a camera move feels right, whether the copy
reads well aloud.

## Shipping a client build

The working file keeps its comments; they are the record of why the deck draws what it draws. The copy
that goes out does not. `scripts/strip_comments.py <in.html> <out.html>` removes JS, CSS and HTML
comments with a state machine, because a deck is full of things that look like comments and are not:
base64 data URIs, URLs inside strings, regex literals. Prove the build before sending: `node --check`
every block, walk every beat for console errors, run the stripper again (a second pass must remove
zero), and diff the client-visible text of both builds. Identical text is the claim you are making.

## Gotchas

- `cmd | tail` (or `| head`, `| grep`) returns the **pipe tail's** exit code, usually 0, and masks a failure
  in `cmd`. Capture the real exit code separately, or check output-file mtimes, before trusting a step.
- **Verify your verifier.** A diff of two harness runs once reported "identical", and it was two identical
  error messages: both runs had failed before producing any output. Assert the harness produced
  non-trivial output, by byte count and a content sample, before trusting any comparison.
- **Sampled checksums lie.** A checksum sampling every nth byte called two renderings identical where a
  full-buffer compare found thousands of differing bytes. Compare whole buffers and report the difference
  as a share of pixels with a max delta.
- **Comments are not inert to static checks.** A `<section>` written inside a JS comment inflates a section
  count, and a beat id mentioned only in comments reads as wired. Strip comments before counting anything
  structural (`verify.py` does).
- Valid syntax is not a working file. A structurally sound blob can still render empty. The simulate step is
  not optional.
- Duplicate registry keys silently shadow (last one wins) with no error. Count a key file-wide before adding
  it; reuse the existing entry if present.
