---
name: scrollytelling
description: Build, extend or verify the gym mood board scroll deck (deck/index.html), an image-led scrollytelling page with three layer types (none for plain statements, figure for renders and plans with numbered boxes and zoom, grid for tagged image tiles with palette swatches) and chapters, on a light warm ground. Owns the engine, the design system and the verification scripts. Use when authoring beats, changing visuals or checking the deck before handover.
---

# Scrollytelling (gym mood board deck)

One scroll-driven HTML page that walks a reader through **vision → floor plan → mood**. Prose cards scroll
on the left; a fixed stage on the right shows the visual for the beat the reader is on. This skill owns the
**artifact**. The words live in the `story` skill; the images and facts live in `moodboard-assets`.

## Kit

- `references/engine_skeleton.html`: the complete, working deck to fork. Already forked to `deck/index.html`.
- `references/engine.md`: how the engine works: `PHASES` → `enter()`, the three layer types, boxes and zoom
  maths, chapters, scroll controller, data binding, image performance, debugging.
- `references/design_system.css`: tokens and components, generated from the deck by `sync_kit.py`.
- `references/design.md`: the visual principles, so changes stay on-system.
- `scripts/verify.py deck/index.html [--unused]`: static checks. **Run after every edit.** `--unused` lists
  catalogued images no beat shows, which is the shortlist when a beat needs more pictures.
- `scripts/sync_kit.py deck/index.html [--check]`: rewrite the two reference copies from the deck. **Run
  after every structural or CSS edit**; `verify.py` warns when they are stale.
- `scripts/shotbeat.mjs deck/index.html --beat <step> --out deck/build/<step>.png --launch`: photograph one
  beat in headed Chrome. `--all --out deck/build` shoots every beat at 1600x1000 and 390x844 in one
  browser: that is the handover pass.

## Method: a new beat or chapter

1. **Story first, no HTML.** The beat list is agreed in `story/storyboard.md` (via `story`) before any edit.
2. **Assets and facts second.** Images catalogued and web-sized, boxes traced in `story/annotations.json`, numbers
   in `story/facts.json`, then `python .claude/skills/moodboard-assets/scripts/build_data.py`.
3. **Wire each beat at both points, together:** a `<section class="step" data-step="X" data-chapter="…">` card,
   and a `PHASES.X` spec (`layer` plus `items` / `frames` + `group`). A step with no spec renders nothing;
   `verify.py` fails on it. A new *kind* of visual means a new layer type in `enter()` (see `engine.md`).
4. **Style** only with the tokens and components in the design system. One accent, square boxes.
5. **Verify and sync.** `verify.py` must PASS, `sync_kit.py` after any CSS or structural change. Before
   handover, `shotbeat.mjs --all` and look at the PNGs. Then a person judges what no script can.

## Method: revising a built deck (the common case)

Most work arrives as "deck 09: swap that image, drop the tile line, make the text longer". Beat numbers in
the request are the **on-screen numbers**, which are positions, not ids: count sections to find the
`data-step`, and say the id back in the reply so a mis-count surfaces at once.

1. Restate the change per beat: which images in, which out, which sentences change.
2. Edit the section card and its `PHASES` entry in the same pass, then `story/storyboard.md` (its table row
   and any key-copy line). The board is the agreed running order, so `verify.py` fails when the two drift.
3. Removing an image from a beat does not remove it from the project: it stays catalogued and shows up
   under `--unused`.
4. `verify.py` → `sync_kit.py` → shoot the beats that changed, at both sizes, and look.
5. Report what changed, and re-surface open decisions instead of deciding them silently.

## Rules for this deck

- **No em dashes in visible copy** (also in titles/alt text). Use a colon, comma or period.
- **One idea, one card, one visual per beat.**
- **Every image has real alt text** from `catalog.json`; decorative marks are `aria-hidden`.
- **No typed numbers in markup.** Every figure is `<span data-bind="fact_id">` bound from `facts.json`;
  an assumption renders with a visible `*` marker. No fact lives only on hover or only in motion.
- **No `fetch()`.** The deck must open by double-click (file://); data is inlined by `build_data.py`.
- **Animate `transform` and `opacity` only.** Figure zoom is one CSS transform on `.plan-canvas`.
- **Respect `prefers-reduced-motion`**: no zoom easing, no staggered reveal, same content.
- **No scroll-jacking.** Native scroll and keyboard work; the rail is a shortcut, not a controller.
- **Contrast**: body text ≥ 4.5:1 on its ground. `--ink-faint` is for large or decorative text only.
- **Responsive at 720px**: cards drop to the bottom, the visual takes the top half. A long card starts
  below the visual (`section.step:not(.center){padding-top:58vh}`), never over it.
- **Grids leave no orphan tile.** Choose `cols` (or a `size:"big"`/`"wide"` tile) so the last row fills:
  3 or 6 tiles in 3 columns, 4 in 2. `verify.py` warns on an orphan. Captions are hidden on small tiles.
- **Web images only** in the deck (`assets/web/`), never `assets/source/` originals.
- **Floor plans have no background.** Transparent WebP from `make_web.py`, no frame, outline-only boxes.
- **Beats are numbered by the engine** (eyebrow counter, `05 / 14` in the top bar); never type them.
- **Brand stays in the corner.** `.corner-logo` is fixed (bottom right on desktop, top centre below 720px,
  where the bottom right would cover the visual). `enter()` writes `body[data-step]`, which is how the
  closing beat fades the corner logo out while the centred logo scales in. Brand files live in
  `assets/brand/`, outside `assets/source/`, so the catalog never asks for alt text on a logo.

## What still needs a person

Whether the composition works, whether a zoom lands where the eye expects, whether the copy reads well
aloud, and whether the mood selection says what the client should feel. Say so when handing over.

## Traps

- **Patching a script through a shell heredoc corrupts it.** A `\b` in a regex became a literal backspace
  and silently disabled four checks. Write the patch script to the scratchpad and run it by path, or use
  the Edit tool, and negative-test every new check by breaking the deck on purpose.
- **Headless Chrome delivers no IntersectionObserver entries**: every beat looks dead. Always headed
  (`shotbeat.mjs` does this).
- **A beat photographed too early** shows a transition, or the intro instead of the beat. `shotbeat.mjs`
  re-scrolls after the images settle and prints `SCENE MISMATCH` when the deck disagrees with the file
  name; read that line before trusting a shot.
- **Boxes are fractions of the web image** (plans trimmed), not of the original 7016px sheet (`make_web.py` trims).
- **After adding images, rerun `catalog.py` → `make_web.py` → `build_data.py`**, or the deck points at nothing.
- **A broken command chain hides everything after it.** One crashing script (a `Thumbs.db` in a folder) left
  the deck showing stale data while the screenshots looked fine. Read the whole log, not the last line.
