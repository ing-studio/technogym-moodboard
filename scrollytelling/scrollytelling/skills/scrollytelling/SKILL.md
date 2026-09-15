---
name: scrollytelling
description: Build or extend a map scrollytelling deck (dark by default, light supported) — MapLibre + Canvas overlay engine, scroll-driven story beats, geo data over polygons and geopackages. Owns the engine, the visual style, frame-rate measurement and safe editing. Self-contained and project-agnostic.
---

# Scrollytelling

Build (or extend) an animated, scroll-driven story deck: a fixed MapLibre basemap (dark by default, light
a supported fork) with a synced Canvas-2D overlay, geo layers (polygons, geopackages, flows) drawn over
it, and prose cards that fade in on the left as the reader scrolls. This skill owns the **artifact**: the
engine, the visual style, and the technique for editing the single file safely. **$ARGUMENTS** = the topic
or dataset. If a deck already exists in the current project, name it and extend it.

This skill is **self-contained** and works in any project. The `references/` kit:
- `engine_skeleton.html` — a complete, minimal, forkable deck. Copy it and build on it.
- `engine_architecture.md` — how the engine works, with inlined code for every mechanism.
- `design_system.css` — the token system + card / chrome / overlay components (sharp-edged house UI).
- `design_language.md` — the visual principles (why the look is what it is) so a fork stays on-system.
- `map_grammar.md` — the grammar for data over the map: polygons/geopackages, movement, palette, camera.
- `html_surgery.md` — how to edit the giant single file precisely, prove it, and cut a client build.
- `performance.md` — how to measure frame behaviour, what canvas layers actually cost, and the traps that
  make a stalling deck look fine.

The `scripts/` kit:
- `verify.py <deck.html>` — static checks: `node --check` every inline script, banned-token sweep,
  section/dispatch coverage, plus lints for `Math.random` and the quadratic `closePath`. Run after every
  edit.
- `frameprobe.mjs <deck.html> --launch --walk --glide` — dynamic checks in a real browser: frame
  percentiles, stalls, long tasks, console errors, per-beat card reveal.
- `strip_comments.py <in.html> <out.html>` — the client build, comments removed, nothing else changed.

## The concerns, split across skills

This skill is the **artifact**. Three sibling skills own the rest; load them for their stage:
- **`verify-scrolly`** — the pre-ship pass: static, frames, pixels. On request, and before it ships.
- **`narrative-craft`** — the story: the arc, the per-beat copy, the pivot words, the linking. Draft the
  beat list there **before** any code.
- **`data-story-binding`** — the numbers: profile the data folder, grade every figure, bind it to one
  registry so nothing drifts. Its `scripts/profile.py` turns a GB folder into a small profile.

## Method

1. **Story first, no code.** Draft the beat list with `narrative-craft` (arc + per-beat template). One
   idea, one card component, one map scene per beat. Do not open the HTML until the beats are agreed.
2. **Numbers second.** Build the registry and contract with `data-story-binding`: every on-screen figure
   is data bound to one `window.__DATA__` (or `__DECK__`) blob, graded, never a literal in the markup.
   Inline the blob so the file is double-clickable and works offline except for map tiles.
3. **Fork the artifact.** If the project has a house deck, fork **that** (it carries live data wiring).
   Only reach for `references/engine_skeleton.html` when starting fresh.
4. **Wire every beat, and declare the wiring in ONE place.** Forking is fine, but a beat renders blank
   silently unless all three points agree, so keep them declared together and checked, never scattered:
   - (a) the `<section class="step" data-step="X">` card in the HTML,
   - (b) a `PHASES.X` scene spec (`{ geo, cam, …flags }`),
   - (c) the flag handling in `enter()` / `draw()`.
   After any beat change run `scripts/verify.py`: every `data-step` must have a matching scene spec and no
   duplicate keys. This is the resolution of the old "fork vs declare" tension: fork the file, but treat
   the beat→scene map as a declared, checked contract, and back-port engine fixes deliberately.
5. **Style and draw.** Use the tokens/components in `design_system.css` and the principles in
   `design_language.md`; draw geo and motion per `map_grammar.md`. For any chart, stat tile, KPI row, or
   meter inside the deck, defer palette and mark specs to the **`dataviz`** skill so the chart marks and
   the deck chrome read as one system. `design_system.css` owns the chrome; `dataviz` owns the chart marks.
6. **Verify, then hand over.** `verify.py` after every edit, for syntax and structure. The browser
   passes — `frameprobe.mjs` for frame behaviour, and a screenshot of a named beat — are the
   **`verify-scrolly`** skill's, and they run ON REQUEST and before the file ships, not after every
   edit. That skill owns when to run which pass and how to read the numbers; `performance.md` owns what
   the frame numbers mean. Then a person, for taste. Budget a new canvas layer before
   building it: the costs are in `performance.md` and the difference between a good and a catastrophic
   version of the same layer is routinely three orders of magnitude.

## Engine in one paragraph

Single self-contained HTML: MapLibre CDN → data blob → `<style>` tokens → `<body>` with a fixed
`#ff-stage` (map `#ff-mapgl` + glow canvas `#ff-fx`), a `#scrim`, fixed chrome, and `#ff-scroller` holding
N `<section data-step>` cards → one IIFE. The IIFE = utils (incl. seeded `mulberry32`) → cached
radial-gradient glow sprites → MapLibre (dark-matter, `interactive:false`) → a **`PHASES` registry**
(data-step → scene-flag spec) → **`enter(id)`** writes flags + birth-timestamps into a mutable `state` →
**`draw()`** gates each canvas layer on `state`, composited per the ground, synced to the map via
`map.on("render")` + `map.project()` → a scroll controller that observes which section holds mid-viewport,
reveals its card, drives the rail, and dispatches via a debounced `enter()`. See `engine_architecture.md`.

## House rules / gotchas

- **No em dashes in visible text.** Use a colon, a parenthetical, or a period. (JS comments may keep them.)
  `verify.py` sweeps for these.
- **Sharp-edged, defined boxes.** Square corners, hairline borders, one accent on dark. See
  `design_language.md`; do not reintroduce rounded/soft UI per deck.
- **Seeded RNG** (`mulberry32`) for every random placement so frames are deterministic. Never
  `Math.random()`.
- **Compositing follows the ground**: additive `"lighter"` on a dark deck, `"source-over"` throughout on a
  light one, where additive draws nothing. Reset to `"source-over"` for HTML labels either way. Cache one
  radial-gradient sprite per RGB. See `design_language.md`.
- **Map is passive**: `interactive:false`; the canvas overlay syncs via `map.on("render", draw)` +
  `map.project()`. Cull off-screen points; cache projected coordinates keyed on the camera transform for
  any layer over a few thousand vertices.
- **Batch polygons into one path** and close rings with `lineTo`, never `closePath()`: path building is
  quadratic in closed subpaths. `performance.md`.
- **Gate the render loop**: hidden tab, scroll-quiet window, frame cap. An ungated overlay repaints at
  60 fps for as long as a geo beat is on screen and competes with the scroll.
- **Static unless told to move**: consecutive beats with the same framing must not re-issue a camera move;
  hold the frame and change only layers or text.
- **Needs internet** for MapLibre GL + CDN basemap tiles; show a graceful fallback.
- **Responsive** at the 720px breakpoint: cards move to the bottom, any right-side viz panel hides.
- **Never diagnose a scroll deck from headless card state.** Headless Chrome delivers zero
  IntersectionObserver entries, so every card reports as never revealed and every beat as never
  activated. That looks exactly like a broken controller and is only the harness.
- **Measure, then hand over.** `verify.py` covers syntax and structure and is cheap enough to run always;
  `frameprobe.mjs` and a beat screenshot cover frame rate, console errors and geometry, and belong to
  the `verify-scrolly` skill, which is invoked rather than run by reflex. What still needs a person:
  whether the composition works, whether a camera move feels right, whether the copy reads well aloud. The skeleton is derived from
  production decks but has not itself been rendered here, so smoke-test it after forking.
- **Client build**: ship a comment-stripped copy (`strip_comments.py`), prove the client-visible text is
  identical to the source build, and keep the working file's comments as the engineering record.

## Project slot

`references/project/` holds this project's real deck HTML to fork, brand assets, and any base map override.
Nothing project-specific belongs in this SKILL or the other references.
