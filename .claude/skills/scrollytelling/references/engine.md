# Engine

How `deck/index.html` works. Read with `engine_skeleton.html` open.

## File anatomy

```
<head>
  <script>window.__DATA__ = /*__DATA__*/{…}/*__END__*/;</script>   # written by build_data.py, never by hand
  <style> design system (inlined copy) </style>
<body>
  #stage                      fixed, full viewport
    #layer-hero               stacked full-bleed <img>, one .on
    #layer-plan > .plan-frame > .plan-canvas  <img> + <svg viewBox 0 0 1 1> areas + #plan-labels
    #layer-mood > .mood-grid  <figure class="tile"> × N
  #scrim                      left legibility wash, on for hero only
  .topbar  #rail  #hint       chrome
  <main id="scroller">        N × <section class="step" data-step="X"><div class="card">…
  <script> one IIFE: helpers → PHASES → layer functions → enter() → hydrate() → scroll controller
```

`__DATA__` shape (built from `assets/catalog.json`, `story/areas.json`, `story/facts.json`):
```js
{ images: { "mood-08-kettlebell-wall-oak": { src:"../assets/web/03-mood/….webp", alt, title, tags,
            palette:["#…"], web_w, web_h, chapter, orientation } },
  areas:  { "plan-level-02": [ { id:"cardio", name:"Cardio", box:[x,y,w,h], notes } ] },
  facts:  { "level_02_stations": { value:24, display:"24", source:"count on plan-level-02", assumed:false } } }
```

## PHASES → enter()

`PHASES` maps each `data-step` to a scene spec. It is the single place a beat's visual is declared.

| layer | fields | what happens |
|---|---|---|
| `hero` | `images: [id…]` | full-bleed crossfade every 5 s (off under reduced motion, paused in a hidden tab) |
| `plan` | `level: id`, `area: id \| null` | plan fitted into the free area; with `area`, one transform zooms to it and dims the rest |
| `mood` | `images: [id…]` | grid built once per image set; staggered reveal; caption + 4 palette swatches |

`enter(id)` returns early if the beat is already active, stops the hero timer, switches the `.on` layer,
then calls the layer function. Layer functions rebuild DOM only when their image set changes, so
scrolling back and forth costs nothing.

**Adding a beat** = a `<section data-step="X">` + `PHASES.X`. Consecutive plan beats on the same `level`
with different `area` values give a guided tour: the image stays, only the transform moves.

**Adding a layer type** (e.g. before/after compare): a `#layer-NAME` in `#stage`, add `NAME` to the
`showLayer` list, an `enterNAME(spec)` function, one `if` in `enter()`, and components in the design system.
Keep it to transform/opacity animation.

## Plan zoom

`.plan-frame` (overflow hidden) and the canvas inside it are sized to fit the free area (right 58% of the viewport; top half below 720px) at the plan's
aspect ratio. Area boxes are fractions (0-1) of the **trimmed web plan**. To focus area `[x,y,w,h]` in a
canvas of `W×H` px:

```
s  = min(4, 0.85 * min(1/w, 1/h))           // fill 85% of the canvas, cap at 4×
tx = W/2 - (x + w/2) * W * s                 // centre the area
ty = H/2 - (y + h/2) * H * s
transform: translate(tx, ty) scale(s)        // transform-origin 0 0
```
The frame clips the zoomed canvas, so it never spills under the card or rail. Labels counter-scale with `--inv = 1/s` so text stays the same size; SVG strokes use
`vector-effect: non-scaling-stroke`. `fitPlan` reruns on resize.

To trace a box: open the web plan (`assets/web/02-floor-plan/<id>.webp`) in any viewer that shows pixel
coordinates, divide by `web_w`/`web_h` from `catalog.json`.

## Scroll controller

- **Two IntersectionObservers, no per-scroll layout reads.** `centerIO` (zero-height line at mid-viewport)
  picks the active section; a fling delivers several entries out of order, so it takes the latest `time`.
  `cardIO` (-20% margins) toggles `.card.in`.
- **140 ms debounced commit.** The rail updates at once, but `enter()` fires only for the beat the reader
  settles on, so flicking past five beats does not start five zooms.
- Without IntersectionObserver every card is shown (content never depends on the script working).
- The first beat's scene is entered on boot, before any scroll.

## Facts

`hydrate()` fills every `[data-bind]` from `D.facts`: `display` if present, else `value`. `assumed: true`
adds `.assumed` (visible `*`) and a title with the source note. A missing id renders `?` highlighted red,
and `verify.py` fails on it before anyone sees it.

## Image performance

- Only `assets/web/` derivatives: photos ≤1600 px, plans ≤3200 px wide (sharp at 2-4× zoom), WebP q82.
  The whole image set is ~5 MB; a deck showing 15-20 images loads well under that.
- `width`/`height` attributes are set from the catalog so nothing shifts while images load.
- `decoding="async"` on every image; the hero and mood DOM is built on first entry, so later chapters do
  not download until the reader gets near them.
- Animate transform/opacity only; never width/height/top/left in a transition.

## Debugging

`window.__APP` = `{state, PHASES, enter, data}`. In the console: `__APP.enter("plan")` forces a scene;
`__APP.state.id` shows the active one. If a beat is blank: is `data-step` in PHASES (verify.py), do its image
ids exist in `__APP.data.images`, did `build_data.py` run after the last `make_web.py`?
