# Engine

How `deck/index.html` works. Read with `engine_skeleton.html` open.

## File anatomy

```
<head>
  <script>window.__DATA__ = /*__DATA__*/{…}/*__END__*/;</script>   # written by build_data.py, never by hand
  <style> design system (inlined copy) </style>
<body>
  #stage                      fixed, full viewport
    #layer-figure > #figure   .fig × 1-2 (label + .plan-frame > .plan-canvas: img, svg boxes, labels) + .strip
    #layer-grid > .grid       <figure class="tile"> × N
  .topbar (#chapter)  #rail  #hint   chrome
  <main id="scroller">        N × <section class="step" data-step="X" data-chapter="01 Vision"><div class="card">…
  <script> one IIFE: helpers → PHASES → tile/figure/grid functions → enter() → hydrate() → scroll controller
```

`__DATA__` shape (built from `assets/catalog.json`, `story/annotations.json`, `story/facts.json`):
```js
{ images: { "vision-01-cardio-gallery-oak-ceiling": { src:"../assets/web/01-vision/….webp", alt, title, tags,
            palette:["#…"], web_w, web_h, chapter, orientation } },
  annotations: { "plan-level-b1": [ { id:"continuity", group:"issues", n:"3", name:"Continuity", box:[x,y,w,h] } ] },
  facts:  { "vision_images": { value:7, display:"7", source:"assets/catalog.json …", assumed:false } } }
```

## PHASES → enter()

`PHASES` maps each `data-step` to a scene spec. It is the single place a beat's visual is declared.

| layer | fields | what happens |
|---|---|---|
| `none` | | no visual: plain ground (intro, statements) |
| `figure` | `frames:[{image, group?, label?, col?}]`, `widths?`, `focus?`, `strip?:[{image \| text, tag}]` | images with the boxes of `group` from annotations; frames without `col` sit side by side (stacked below 720px); frames with `col` stack in that column and `widths` weights the columns (the building: levels 5 to 2 in column 0, -1 and -2 in column 1); `focus` zooms to a box (single frame only); `strip` is a row of tagged tiles under the frames. Floor plans get `.sheet`: transparent drawing, no frame, outline-only boxes |
| `grid` | `items:[{image, tag?, size?: "big" \| "wide"}]`, `cols?`, `captions?`, `swatches?` | tile grid built once per beat, staggered reveal; tag top-left, caption + palette swatches bottom |

`enter(id)` returns early if the beat is already active, switches the `.on` layer, then builds the layer
for that beat (keyed by step id, so scrolling back and forth rebuilds nothing twice in a row).

**Adding a beat** = a `<section data-step="X" data-chapter="…">` + `PHASES.X`. Consecutive figure beats on
the same plan with different `focus` values give a guided tour.

**Adding a layer type**: a `#layer-NAME` in `#stage`, add `NAME` to `LAYERS` (engine) and to `LAYERS` in
`verify.py`, an `enterNAME(spec, id)` function, one `if` in `enter()`, components in the design system.
Keep it to transform/opacity animation.

## Boxes and zoom

Boxes are `[x,y,w,h]` fractions of the **web** image (plans are trimmed of white sheet). `group` picks the
set a beat shows, so one image can carry layers, aspects and issues. `n` is the label (number or letter);
boxes sharing an `n` show the name once.

Frames are sized by `layoutFigure()` into the free area (right 58% of the viewport; top half below 720px),
minus the strip. To focus box `[x,y,w,h]` in a frame of `W×H` px:

```
s  = min(4, max(1, web_w / W), 0.85 * min(1/w, 1/h))   // cap at 4× and at the image's own pixels
tx = W/2 - (x + w/2) * W * s
ty = H/2 - (y + h/2) * H * s
transform: translate(tx, ty) scale(s)                  // transform-origin 0 0
```
The pixel cap means a 1200 px render never upscales into blur; only large plans really zoom. The frame
clips the canvas. Labels counter-scale with `--inv = 1/s`; strokes use `vector-effect: non-scaling-stroke`.
`layoutFigure` reruns on resize.

## Chapters

Each section carries `data-chapter`. The top bar shows the active chapter at once (not debounced); the rail
leaves a gap where the chapter changes. `verify.py` fails on a section without it.

Beats are numbered automatically: a CSS counter puts the beat number (01, 02 …) at the start of every
eyebrow, and the top bar shows `05 / 12` beside the chapter. Never type beat numbers into copy; moving a
section renumbers everything.

## Scroll controller

- **Two IntersectionObservers, no per-scroll layout reads.** `centerIO` (zero-height line at mid-viewport)
  picks the active section; a fling delivers several entries out of order, so it takes the latest `time`.
  `cardIO` (-20% margins) toggles `.card.in`.
- **140 ms debounced commit.** The rail and chapter update at once, but `enter()` fires only for the beat
  the reader settles on.
- Without IntersectionObserver every card is shown (content never depends on the script working).
- The first beat's scene is entered on boot, before any scroll.

## Facts

`hydrate()` fills every `[data-bind]` from `D.facts`: `display` if present, else `value`. `assumed: true`
adds `.assumed` (visible `*`) and a title with the source note. A missing id renders `?` highlighted red,
and `verify.py` fails on it before anyone sees it.

## Image performance

- Only `assets/web/` derivatives: photos ≤1600 px, plans ≤3200 px wide, WebP q82.
- `width`/`height` attributes are set from the catalog so nothing shifts while images load.
- `decoding="async"` on every image; figure and grid DOM is built on entry, so later beats do not
  download until the reader gets near them.
- Animate transform/opacity only; never width/height/top/left in a transition.

## Debugging

`window.__APP` = `{state, PHASES, enter, data}`. In the console: `__APP.enter("plan")` forces a scene;
`__APP.state.id` shows the active one. If a beat is blank: is `data-step` in PHASES (verify.py), do its image
ids exist in `__APP.data.images`, does its `group` have boxes in `__APP.data.annotations`, did
`build_data.py` run after the last `make_web.py`?
