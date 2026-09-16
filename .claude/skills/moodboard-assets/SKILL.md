---
name: moodboard-assets
description: Manage the gym project's images and facts: the chapter folders, the naming scheme, renaming/moving new images with hash checks, assets/catalog.json (titles, alt text, tags, palettes), web-sized derivatives with floor-plan whitespace trimmed, annotation boxes on renders and plans, sourced facts, and inlining all of it into the deck. Use when images are added or renamed, areas or numbers change, or the deck's data needs rebuilding.
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
story/annotations.json         boxes drawn on images (plan areas, render layers, issues)
story/facts.json               every on-screen number with its source
```
Originals in `assets/source/` are never edited, only renamed. Brand files (the client logo and anything
generated from it) live in `assets/brand/`, outside `assets/source/`, so the catalog never demands a title
and alt text for a logo.

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
python .claude/skills/moodboard-assets/scripts/make_web.py           # WebP derivatives; plans trimmed, paper made transparent
python .claude/skills/moodboard-assets/scripts/build_data.py         # inline into deck/index.html
python .claude/skills/scrollytelling/scripts/verify.py deck/index.html
```
Drop new images in `assets/inbox/` first. `organize.py` skips entries already moved, so the map is the
full history. `catalog.py` and `make_web.py` are safe to rerun, and `catalog.py` ignores non-image files
(`Thumbs.db`, `.DS_Store`) rather than crashing on them.

### A new image, end to end

1. **Look at it.** Title, alt text and tags are written after viewing the file, never from the file name.
2. **Screen it.** A third-party logo, a shop sign, a watermark or a recognisable person makes an image
   unusable in a client deck, or usable only once someone clears the rights. Say which it is; never slip
   one in quietly. Images already caught this way: `FYSIK`, `brisafe`, a Xiaohongshu watermark, an athlete
   poster.
3. **Catalogue it**: `catalog.py --check` fails while the title or alt is empty, which is the gate.
4. **Size it and inline it**: `make_web.py` then `build_data.py`, then `verify.py`.
5. A retitled image keeps its id: the id is the file name, so renaming a *title* costs nothing, renaming a
   *file* goes through `organize.py`.

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

## annotations.json

```json
{ "images": { "plan-level-b1": [
  { "id": "continuity", "group": "issues", "n": "3", "name": "Continuity", "box": [0.41, 0.30, 0.12, 0.20] } ] } }
```
- Keyed by image id; works for plans and renders alike.
- `group` is the set a beat shows (`layers`, `issues`, `areas`, …); one image can carry several.
- `n` is the on-stage label (number or letter) and must match the numbered list in the card.
- `box` = `[x, y, w, h]` as fractions of the **web** image (plans already trimmed of white sheet), so pixel
  coordinates from `assets/web/<chapter>/<id>.webp` divided by `web_w`/`web_h`. Check with a screenshot.

## facts.json

```json
{ "facts": { "vision_images": { "value": 7, "display": "7", "unit": "images",
  "source": "assets/catalog.json: images in chapter 01-vision", "assumed": false } } }
```
- Every number on screen is a fact id bound with `data-bind`; nothing typed in the HTML.
- `source` says where it comes from (a plan count, a spec sheet, the client brief). A number with no real
  source is `assumed: true` and shows a visible `*` in the deck.
- Before adding an id, search for it: an existing one is reused, never duplicated.
- When a number changes, change it here only, rebuild, and search the copy for the old value.
