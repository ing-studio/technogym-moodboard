# Design language

The house look, stated as principles so any fork keeps it without re-deriving taste. The tokens and
components that implement this live in `design_system.css`; this file is the *why*, so a new deck reads as
one system with the others.

## The look in one line

Sharp-edged, defined boxes on one ground, one restrained accent, one type scale, generous whitespace. It
should feel engineered and precise, not soft or decorative. Data instrument, not marketing page.

## The ground is a parameter, and it changes the drawing grammar

**Dark is the house default**: near-black surface, ink-on-dark hierarchy, additive glow as the one bright
layer. A deck may instead sit on a **light** ground (a paper-white or warm off-white surface, dark ink),
and that is a supported fork, not a deviation. What must change with it is not only the palette:

- **Compositing.** Additive `lighter` is the whole grammar of a dark deck: overlapping marks sum toward
  white and glow reads as intensity. On light ground it does nothing, because adding light to near-white
  is still near-white. A light deck draws every layer `source-over`, which keeps the same build-up
  behaviour (repeated low-alpha draws converge on the mark colour) while leaving marks visible on paper.
- **Glow stops being available as emphasis.** On light ground weight, edge and a cleared surface do that
  work: a mark that must separate from a busy layer gets its own patch of ground beneath it, not a halo.
- **Contrast inverts, so re-check every mark.** A hue that reads on near-black can fail on paper, and
  lightening a mark to make it "brighter" moves it toward a light ground rather than away from it.

Everything below this line is surface-independent and holds in both.

## Principles

- **Sharp edges.** Square corners on every box: cards, panels, chips, bars, tracks, legend swatches, map
  labels. Rounded corners read as consumer-soft; square reads as precise. The only round things are small
  status or accent dots (a nav dot, an eyebrow dot), which read as indicator lights, not boxes.
- **Definition by line, not shadow.** Separate and frame with crisp hairline borders (`--line`) and a
  slightly stronger rule for framed panels (`--line-strong`). Avoid drop shadows and glows *as structure*;
  the only glow is the additive map layer, which carries data, not chrome. A box is defined by its border,
  not by a blur.
- **One accent.** A single primary accent (house magenta on dark) used sparingly for the pivot, the active
  state, and the one thing that matters per beat. Secondary accents exist only to encode categories (the
  type/hub palette), never for decoration. If everything is accented, nothing is.
- **One type scale.** A single family, a disciplined ramp (hero → h1 → h2 → lede → body → note → label).
  Labels and eyebrows are uppercase, tracked, small. Do not introduce a second display face per deck.
- **Whitespace is structure.** Let cards breathe against the map; the scrim carries legibility so the card
  does not need a heavy background. A boxed `.card.panel` is the exception, for a beat that wants a framed
  block.
- **Ink hierarchy, not many colours.** Four steps of ink (`--ink` → `--ink-faint`, white-based on dark,
  near-black-based on light) do most of the work; reach for an accent only to mean something.

## How this meets the map

The map is the loudest element, so the chrome stays quiet: thin rules, muted labels, square chips. The
data glow is the only bright, animated layer. Map marks and chart marks share the same palette (see the
`dataviz` skill) so a colour means the same thing whether it is a polygon fill, a flow trail, or a bar.

## What NOT to do

- No rounded cards, pill-heavy UI, or soft neumorphic surfaces.
- No second accent colour "to add interest"; interest comes from the data and the motion.
- No drop-shadow stacks to fake depth; depth is the fixed map behind the scrolling cards.
- No gradient text or decorative flourishes on headlines; the one `<em>` pivot is the only emphasis.
