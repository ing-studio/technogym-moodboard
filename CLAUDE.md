# Gym mood board scrollytelling

A scroll story for a gym design project. It shows that a design becomes easier to understand and decide
on when the client's vision, our floor plan and the suggested mood are consolidated into one argument,
and it doubles as a method for building a mood board.

**Core message:** a mood cannot be built from single rooms. The building works as one body, one organism,
so the mood has to run through all of it, made of natural materials (wood, stone, earth, plaster, textile).

Three chapters, in this order:
0. **Intro**: plain ground, the claim and the chapters.
1. **Vision**: the proposed Technogym styling in 3 beats: what is proposed, what we need to look at, what needs
   to be assessed (`assets/source/01-vision`).
2. **Floor plan**: 1 beat: all floors read as one body, one organism, not separate pieces
   (`assets/source/02-floor-plan`).
3. **Mood**: why natural materials, the proposal (wood at the heart, its warmth carried into plaster, stucco and textile), one beat per material (wood; stone and earth;
   lime plaster and warm light; textile, leather and bronze), the list of proposed materials, and bright accents (LED displays, billboards, a bright staircase)
   (`assets/source/03-mood`).

Project specifics (client, claim, areas, numbers) are still to come: see TODOs in `story/brief.md`.

## Layout

```
.claude/agents/scrollyteller.md    orchestrator: brief → assets → storyboard → author → verify → report
.claude/skills/story/              arc, storyboard, copy rules
.claude/skills/moodboard-assets/   naming, catalog, web images, areas, facts, data build (scripts/)
.claude/skills/scrollytelling/     engine, design system, verify.py, shotbeat.mjs
assets/source/                     originals, renamed, never edited
assets/web/                        generated WebP (gitignored)
assets/catalog.json                titles, alt text, tags, palettes per image
story/                             brief.md, storyboard.md, annotations.json, facts.json
deck/index.html                    the deck; deck/build/ holds screenshots (gitignored)
index.html                         the deck bundled as one portable file; what GitHub Pages serves
archive/                           superseded HTML files, kept for the record
```

## Commands (from the project root)

```
python .claude/skills/moodboard-assets/scripts/catalog.py --check
python .claude/skills/moodboard-assets/scripts/make_web.py
python .claude/skills/moodboard-assets/scripts/build_data.py
python .claude/skills/scrollytelling/scripts/verify.py deck/index.html [--unused]
python .claude/skills/scrollytelling/scripts/sync_kit.py deck/index.html   # refresh the skill kit copies
node .claude/skills/scrollytelling/scripts/shotbeat.mjs deck/index.html --beat plan --out deck/build/plan.png --launch
node .claude/skills/scrollytelling/scripts/shotbeat.mjs deck/index.html --all --out deck/build --launch
python .claude/skills/scrollytelling/scripts/build_standalone.py   # -> index.html, one portable file
```
Use `python`, not `python3` (Store stub on this machine). Node 24 is installed.

## House rules

- Storyboard before HTML; a person approves the brief and the storyboard.
- Every on-screen number comes from `story/facts.json` with a source; assumptions show `*`.
- Every image has alt text; no em dashes in visible copy; no `fetch()` (deck opens by double-click).
- Light warm ground, one bronze accent, square boxes, one type family (`.claude/skills/scrollytelling/references/design.md`).
- Floor plans have no background: transparent drawings on the page, outline-only boxes. Beats are numbered by the engine.
- Run `verify.py` after every deck edit and `sync_kit.py` after any CSS or structural one; photograph
  beats with `shotbeat.mjs --all` before handover.
- `story/storyboard.md` is the agreed running order: keep its rows in step with the deck (verify.py checks).
- What goes to the client is the root `index.html`, rebuilt from the deck, never edited by hand.
  Remote: `git@github.com:ing-studio/technogym-moodboard.git`; Pages serves that file from the repo root.
- Brand files live in `assets/brand/`; images carrying a third-party logo, watermark or a recognisable
  person stay out of the deck until the rights are cleared.
- Never edit `assets/source/` or the `__DATA__` blob by hand.
