---
name: moodboard-assets
description: Manage the gym project's images and facts: the chapter folders, the naming scheme, renaming/moving new images with hash checks, assets/catalog.json (titles, alt text, tags, palettes), web-sized derivatives with floor-plan whitespace trimmed, plan area boxes and sourced facts, and inlining all of it into the deck. Use when images are added or renamed, areas or numbers change, or the deck's data needs rebuilding.
---

# Moodboard assets

Every image and every number the deck shows comes through this pipeline, so nothing is typed twice and
nothing drifts. Run commands from the project root with `python` (not `python3`, which is a Store stub here).

## Folders

```
assets/source/01-vision/       Technogym renders: the machinery they imagine
assets/source/02-floor-plan/   plan sheets, one per level
assets/source/03-mood/         the suggested atmosphere
assets/web/                    generated WebP derivatives (gitignored, rebuild any time)
assets/catalog.json            one entry per image: measured fields + hand-written title/alt/tags
assets/rename-map.json         input for organize.py (old path → new name + title/alt/tags)
assets/rename-log.csv          what moved where, with sha256
story/areas.json               plan areas per level
story/facts.json               every on-screen number with its source
```
Originals in `assets/source/` are never edited, only renamed.

## Naming

`<chapter>-<nn>-<descriptor>.<ext>`, lowercase kebab-case ASCII.
- `vision-01-cardio-gallery-oak-ceiling.png`
- `plan-level-b2.jpg` … `plan-level-05.jpg` (`b` = below ground)
- `mood-08-kettlebell-wall-oak.jpg`

Descriptor: 2-4 words, subject + defining material or feature, written after looking at the image.
Mood numbers run in theme order (training floor, functional, studio, details, changing, wellness,
reception, materials); new images take the next free number rather than renumbering.

## Pipeline

```
python .claude/skills/moodboard-assets/scripts/contact_sheet.py assets/inbox --out _review/inbox   # look
#   add entries to assets/rename-map.json (old: "assets/inbox/<file>")
python .claude/skills/moodboard-assets/scripts/organize.py --plan    # validate, write log
python .claude/skills/moodboard-assets/scripts/organize.py --apply   # move, verify hashes, seed catalog
python .claude/skills/moodboard-assets/scripts/catalog.py --check    # measure, keep hand fields, fail on empty alt
python .claude/skills/moodboard-assets/scripts/make_web.py           # WebP derivatives, plan trim
python .claude/skills/moodboard-assets/scripts/build_data.py         # inline into deck/index.html
python .claude/skills/scrollytelling/scripts/verify.py deck/index.html
```
Drop new images in `assets/inbox/` first. `organize.py` skips entries already moved, so the map is the
full history. `catalog.py` and `make_web.py` are safe to rerun.

## catalog.json entry

```json
{ "id": "mood-08-kettlebell-wall-oak", "file": "assets/source/03-mood/mood-08-kettlebell-wall-oak.jpg",
  "chapter": "03-mood", "title": "Kettlebell wall", "alt": "Functional room with …",
  "tags": ["functional", "storage", "oak"], "w": 736, "h": 920, "bytes": 58997,
  "orientation": "portrait", "palette": ["#…"], "sha256": "…", "original": "02.jpg",
  "web": "assets/web/03-mood/mood-08-kettlebell-wall-oak.webp", "web_w": 736, "web_h": 920 }
```
Hand-written: `title` (2-4 words, no em dash), `alt` (what is visible, one sentence, no "image of"), `tags`
(one area tag from the arc list plus materials). Everything else is measured.

## areas.json

```json
{ "levels": { "plan-level-02": [
  { "id": "cardio", "name": "Cardio", "box": [0.08, 0.05, 0.30, 0.22], "notes": "treadmills along windows" } ] } }
```
`box` = `[x, y, w, h]` as fractions of the **web** plan image (already trimmed of white sheet), so
pixel coordinates from `assets/web/02-floor-plan/<id>.webp` divided by `web_w`/`web_h`.

## facts.json

```json
{ "facts": { "level_02_stations": { "value": 24, "display": "24", "unit": "stations",
  "source": "counted on plan-level-02", "assumed": false } } }
```
- Every number on screen is a fact id bound with `data-bind`; nothing typed in the HTML.
- `source` says where it comes from (a plan count, a spec sheet, the client brief). A number with no real
  source is `assumed: true` and shows a visible `*` in the deck.
- Before adding an id, search for it: an existing one is reused, never duplicated.
- When a number changes, change it here only, rebuild, and search the copy for the old value.
