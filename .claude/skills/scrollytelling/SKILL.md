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
- `references/design_system.css`: tokens and components (the skeleton inlines a copy; keep them in sync).
- `references/design.md`: the visual principles, so changes stay on-system.
- `scripts/verify.py deck/index.html`: static checks. **Run after every edit.**
- `scripts/shotbeat.mjs deck/index.html --beat <step> --out deck/build/<step>.png --launch`: photograph a beat
  in headed Chrome. Run before handover, or after changing engine JS, layout or a plan area.

## Method

1. **Story first, no HTML.** The beat list is agreed in `story/storyboard.md` (via `story`) before any edit.
2. **Assets and facts second.** Images catalogued and web-sized, boxes traced in `story/annotations.json`, numbers
   in `story/facts.json`, then `python .claude/skills/moodboard-assets/scripts/build_data.py`.
3. **Wire each beat at both points, together:** a `<section class="step" data-step="X" data-chapter="…">` card,
   and a `PHASES.X` spec (`layer` plus `items` / `frames` + `group`). A step with no spec renders nothing;
   `verify.py` fails on it. A new *kind* of visual means a new layer type in `enter()` (see `engine.md`).
4. **Style** only with the tokens and components in the design system. One accent, square boxes.
5. **Verify.** `verify.py` must PASS. Before handover, shoot every beat with `shotbeat.mjs` and look at
   the PNGs, at 1600x1000 and at 390x844. Then a person judges what no script can.

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
- **Responsive at 720px**: cards drop to the bottom, the visual takes the top half.
- **Web images only** in the deck (`assets/web/`), never `assets/source/` originals.
- **Floor plans have no background.** Transparent WebP from `make_web.py`, no frame, outline-only boxes.
- **Beats are numbered by the engine** (eyebrow counter, `05 / 12` in the top bar); never type them.

## What still needs a person

Whether the composition works, whether a zoom lands where the eye expects, whether the copy reads well
aloud, and whether the mood selection says what the client should feel. Say so when handing over.

## Traps

- **Headless Chrome delivers no IntersectionObserver entries**: every beat looks dead. Always headed
  (`shotbeat.mjs` does this).
- **A beat photographed too early** shows a transition. `shotbeat.mjs` waits for images plus `--hold`.
- **Boxes are fractions of the web image** (plans trimmed), not of the original 7016px sheet (`make_web.py` trims).
- **After adding images, rerun `catalog.py` → `make_web.py` → `build_data.py`**, or the deck points at nothing.
