# Gym mood board scrollytelling

A scroll story for a gym design project. It shows that a design becomes easier to understand and decide
on when the client's vision, our floor plan and the suggested mood are consolidated into one argument,
and it doubles as a method for building a mood board.

Three chapters, in this order:
1. **Vision**: the Technogym machinery and spaces the client imagines (`assets/source/01-vision`).
2. **Floor plan**: our plan, broken into areas and specifics (`assets/source/02-floor-plan`, `story/areas.json`).
3. **Mood**: the atmosphere we suggest (`assets/source/03-mood`).

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
story/                             brief.md, storyboard.md, areas.json, facts.json
deck/index.html                    the deck; deck/build/ holds screenshots (gitignored)
```

## Commands (from the project root)

```
python .claude/skills/moodboard-assets/scripts/catalog.py --check
python .claude/skills/moodboard-assets/scripts/make_web.py
python .claude/skills/moodboard-assets/scripts/build_data.py
python .claude/skills/scrollytelling/scripts/verify.py deck/index.html
node .claude/skills/scrollytelling/scripts/shotbeat.mjs deck/index.html --beat plan --out deck/build/plan.png --launch
```
Use `python`, not `python3` (Store stub on this machine). Node 24 is installed.

## House rules

- Storyboard before HTML; a person approves the brief and the storyboard.
- Every on-screen number comes from `story/facts.json` with a source; assumptions show `*`.
- Every image has alt text; no em dashes in visible copy; no `fetch()` (deck opens by double-click).
- Light warm ground, one bronze accent, square boxes, one type family (`.claude/skills/scrollytelling/references/design.md`).
- Run `verify.py` after every deck edit; photograph beats with `shotbeat.mjs` before handover.
- Never edit `assets/source/` or the `__DATA__` blob by hand.
