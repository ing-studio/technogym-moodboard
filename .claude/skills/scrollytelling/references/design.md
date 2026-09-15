# Design principles

The deck presents a mood board, so the chrome must stay quieter than the photography. Tokens and
components: `design_system.css`.

## The look in one line

Warm paper ground, dark warm ink, one bronze accent, square boxes defined by hairlines, one type family,
generous space. It should read like a well-made architect's presentation, not a marketing site.

## Principles

- **The images are the colour.** Chrome uses the ink ramp and one accent (`--accent`, bronze). The accent
  marks the pivot word, the active rail dot, eyebrows and plan areas. If a second colour seems needed, it
  should come from the image palette swatches, not the UI.
- **Light warm ground.** `--bg #f4efe7` matches the stone, oak and plaster in the mood set. Flattened PNGs
  use the same colour (`GROUND` in `make_web.py`), so edges never show a white box.
- **Square and defined.** Square corners on cards, tiles, labels, swatches. Separation by 1 px hairlines
  (`--line`, `--line-strong`), never drop shadows. Only indicator dots are round.
- **One type family, one ramp.** h1 → h2 → lede → body → note → label. Eyebrows and labels uppercase,
  tracked, small. Exactly one italic `<em>` per headline, in the accent colour.
- **Photography gridded or framed by a hairline, never decorated.** Grid tiles crop with `object-fit: cover`;
  a render in a figure keeps its full frame so its boxes stay true. Cards sit on the plain ground beside the
  visual, never over a photo on desktop.
- **Plans and renders are read, not admired.** White sheet or full image, hairline outline, boxes as
  translucent accent fills with a crisp stroke, labels as small solid accent chips carrying the same number
  or letter as the card list. Zoom, do not pan around.
- **Plain ground is a visual too.** A statement beat (`none`) uses space and type only.
- **Ink hierarchy does the work.** `--ink` for headlines, `--ink-dim` for body, `--ink-mute` for notes and
  labels. `--ink-faint` (3.4:1) never carries text a reader must read.

## Don't

- No rounded cards, pills, soft shadows or gradients as decoration.
- No second accent colour, no gradient text.
- No text over a photo without a panel behind it.
- No decorative motion: movement only when the scene changes (fade, zoom, reveal).
