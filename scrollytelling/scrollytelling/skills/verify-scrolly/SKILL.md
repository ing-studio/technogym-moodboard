---
name: verify-scrolly
description: Verify a scroll deck before it ships — static checks, frame behaviour in a real headed browser, and a screenshot of a named beat. Run ON REQUEST only, and always before a deck goes to a client. Project-agnostic.
---

# verify-scrolly

Prove a scroll-driven deck still runs, still holds its frame rate, and still draws what the data says.
**$ARGUMENTS** = the deck file, and optionally the beats to photograph.

## When to run it

**On request, and before the file leaves the building.** Not after every edit. A browser pass costs a
launched Chrome and about a minute, and the vast majority of edits — copy, a figure, a colour — cannot
break anything it measures. Running it every time trains everyone to skim the output, which is worse
than not running it.

Run it when: the user asks; the deck is about to be sent; you changed engine JS, a draw order, or a
payload the map reads; or a static check found something and you need to know if it matters on screen.

Skip it when: you edited prose, a legend label, or a bound figure and `verify.py` passed.

## The three passes

Escalate only as far as the change warrants. Each one costs about ten times the last.

**1. Static.** `verify.py <deck.html>` — `node --check` on every inline script, banned tokens,
section/dispatch coverage, performance lints. Seconds, no browser. Run this after every edit, always.
Compare its output against the previous build's: a NEW warning is the signal, and a deck that has
always carried three warnings still passes with three.

**2. Frames.** `frameprobe.mjs <deck.html> --launch --walk` — per-beat frame median/p90/max, console
errors, card reveal, unbound data stamps. Read `errors:` and `worst frame:` first; those two lines are
the pass. Then read the per-beat table only if one of them is bad.

**3. Pixels.** `scripts/shotbeat.mjs <deck.html> --beat <data-step> --out shot.png [--launch]`, then
open the PNG. This is the only pass that can answer a geometry question: is the marker on the line, did
the layer land where the join says, does the legend still fit the card. Use `--crop x,y,w,h` to inspect
one corner at 2x rather than squinting at a full frame.

`verify.py` and `frameprobe.mjs` live in the `scrollytelling` skill's `scripts/`; that skill owns the
artifact and its tools. This skill owns the *pass* — when to run which, and how to read it.

## Reading it

- **A number with no baseline is not a result.** Frame timings are relative to the harness floor the
  probe prints, and that floor moves with the display and the machine's load. 20 ms against an 8 ms
  floor is fine; the same 20 ms against a 16 ms floor is the deck. Quote both.
- **Percentiles, never the mean.** The median sits at the refresh interval whether the deck is healthy
  or stalling. Damage shows in max, and in the frame COUNT: a window that collects 4 frames instead of
  450 is a stall the median will never show you.
- **Diff the whole file against the previous build** and count the changed lines. On a deck that is a
  copy of a shipped build, that count IS the safety net — it should equal the edits you intended and
  nothing else.

## Traps

- **Never diagnose a scroll deck headless.** Headless Chrome renders the map at ~1 fps and delivers
  zero IntersectionObserver entries, so every beat reports as never activated. That reads exactly like
  a broken scroll controller and is only the harness. Headed, on a debug port.
- **`deviceScaleFactor` above 1 kills the tab** on a deck with a full-viewport canvas, and the only
  symptom is the debugger socket closing with code 1006. Crop and upscale instead.
- **Wait twice.** ~10 s for the map's first paint, then ~5 s after scrolling for the animated camera to
  land. A shot taken early photographs a transition and gets read as a bug.
- **Kill the browser you launched.** A detached debug Chrome outlives the session and holds the port,
  and the next run attaches to a stale tab. `pkill -f 'remote-debugging-port=<port>'`.
- **What no pass can judge:** composition, whether a camera move feels right, whether the copy reads
  aloud. Say so when you report, and hand it to a person.
