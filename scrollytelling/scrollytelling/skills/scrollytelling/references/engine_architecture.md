# Engine architecture

How the house scrollytelling engine works, self-contained. The concrete, runnable version of everything below is
`engine_skeleton.html` in this folder — read the two together. The patterns are distilled from production
PerigonAI decks; nothing here depends on any file outside this skill.

## File anatomy (single self-contained HTML)

```
<head>
  <script src=".../maplibre-gl@4.7.1/.js">            # the only hard external dependency
  <script>window.__DATA__ = { … }</script>             # all deck data. Build step? inject into a "/*__DATA__*/ null" marker
  <script>window.__ASSETS__ = { … }</script>           # optional: base64 logos/photos
  <style> … </style>                                   # design_system.css tokens + components
</head>
<body>
  #ff-stage ( .atmos  +  #ff-map(#ff-mapgl + #ff-fx canvas) )   # fixed background stage
  #scrim                                               # left-side legibility gradient
  .topbar / .botbar / #ff-rail / #ff-hint              # fixed chrome
  <main id="ff-scroller">  N × <section class="step" data-step="X"><div class="card">…
  <script> (one IIFE = the whole engine) </script>
</body>
```

## The IIFE, in order

1. **Data alias** — `var D = window.__DATA__` (and `A = window.__ASSETS__` if used).
2. **Utils** — `rgba`, `clamp`, `ease`, `now`, and the seeded PRNG `mulberry32` (used for every random placement so
   frames are deterministic). Geometry as needed: `bbox`, and `pathPos` (constant-speed walk along a polyline with
   cached cumulative lengths).
3. **Glow sprites** — `sprite(col)` caches one 64px radial-gradient canvas per RGB triple; `glowDot(x,y,r,col,a)`
   blits it scaled to `r*5.2` so the halo extends past the nominal radius. This is the whole "glow" look.
4. **Map + canvas** — MapLibre creation (dark-matter, `interactive:false`), `sizeCanvas` at device-pixel-ratio,
   `PR(p)=map.project(p)`, `vis(p)` viewport cull.
5. **`PHASES`** registry, **`enter`**, **`draw`**, **`render`** loop.
6. **Scroll controller** (usually a second `<script>`).

## The dispatch pattern: PHASES → enter → state → draw

This is the core. It scales far better than a growing `if/else` on the scene id.

**`PHASES`** — a plain object keyed by `data-step`; each value is a spec of scene flags. Add camera targets and
scene flags as your deck needs them:
```js
var PHASES = {
  intro: { geo:false },
  dots:  { geo:true, cam:{t:"data"}, dots:true },
  area:  { geo:true, cam:{t:"data"}, dots:true, boundary:true },
  flow:  { geo:true, cam:{t:"flow"}, flow:true },
  outro: { geo:false }
};
```

**`enter(id)`** — reads the spec, records a `bornAt` timestamp (for entrance animation), toggles the map on/off
for geo vs non-geo beats, and moves the camera. In a richer deck, set a *birth timestamp per scene* only on the
flag's rising edge (`if(spec.pings && !state.pings) state.pingBorn = now()`), so animations start once and don't
restart every frame.
```js
function enter(id){
  ensureInit(); var spec = PHASES[id]; if(!spec) return;
  state.mode = id; state.spec = spec; state.bornAt = now();
  if(!spec.geo){ leaveGeo(); return; }     // non-geo beat: hide the map, show photo/plain card
  show(); camTo(spec.cam);
}
```

**`draw()`** — one loop, gates each canvas layer on the spec/state. On a **dark** deck the particle and
boundary layers render under additive `"lighter"`, reset to `"source-over"` before any HTML labels. On a
**light** deck every layer is `"source-over"`: additive compositing inverts into nothing on light ground,
because adding light to near-white is still near-white. See `design_language.md`.
```js
function draw(){
  if(!glReady||!running) return;
  ctx.clearRect(0,0,W,H); ctx.globalCompositeOperation = "lighter";
  if(state.spec){
    if(state.spec.dots)     drawDots(t);
    if(state.spec.boundary) drawBoundary(t);
    if(state.spec.flow)     drawFlow(t);
  }
  ctx.globalCompositeOperation = "source-over";
  // updateLabels(); updateCharts();   // HTML overlays positioned via map.project() go here
}
```

## Camera

A single dispatcher keyed on `cam.t` keeps camera logic out of `enter()`. Each target maps to a bounding box plus
pitch/bearing. Padding is asymmetric because the card occupies the left third.
```js
function camTo(cam){
  if(!cam) return;
  if(cam.t==="data")      fitBounds(dataBB, {pitch:36, bearing:-8,  maxZoom:13.5});
  else if(cam.t==="flow") fitBounds(bbox(D.route), {pitch:44, bearing:-12, maxZoom:15});
  else                    fitBounds(dataBB, {});
}
```
`fitBounds` wraps `map.fitBounds(b, {padding:pad(), duration, maxZoom})`. For fine offsets use
`map.easeTo({center, zoom, pitch, bearing, padding})`.

## Canvas / glow / RNG

- **Map is passive**: `interactive:false`. The canvas `#ff-fx` is sized to the map at DPR. It stays synced by
  `map.on("render", draw)` (fires while the map moves) **plus** a gated `requestAnimationFrame` loop for when the
  map is static (see the three gates under Scroll controller).
- **Projection**: `PR(p) = map.project([lng,lat])` → canvas pixels; cull with `vis(p)` before drawing. For a layer
  of more than a few thousand vertices, project once per camera transform and cache the screen coordinates keyed
  on centre/zoom/bearing/pitch/viewport, so a parked camera reprojects nothing.
- **Determinism**: seed every scatter with `mulberry32(seed)`. Never `Math.random()`.
- **True-metre radii** (optional): project two points `1/111320°` apart and measure the pixel distance to scale
  reach rings to real metres.

## Reusable scene primitives

- **`drawDots`** — staggered glow scatter; `births[i]` gate + `glowDot`.
- **`drawBoundary`** — a glowing polygon (oscillating fill + shadow stroke). Reuse for any country/area/plot outline.
- **`drawFlow`** — a comet: walk `pathPos(route, f)` and lay a fading tail of `glowDot`s behind the head. This ONE
  primitive covers every motion scene (entries/exits, trajectories, city flows, a hero trip) — just feed it
  different routes and a pool.
- Richer decks add: staggered store discs sized by a value, pulsing catchment rings, choropleth via a MapLibre
  fill layer toggled on one beat, animated DOM bar charts, HTML label chips positioned by `map.project()`.

## Scroll controller

**Two IntersectionObservers, and nothing that measures the DOM per scroll frame.** The obvious version
loops every section through `getBoundingClientRect()` on every scroll frame; that is layout work
proportional to deck length, on the hot path, and it is the classic source of scroll jank. An observer
does the same job off the hot path, and a fast fling coalesces its callbacks, which throttles the camera
work for free.

```js
var centerIO = new IntersectionObserver(function(ents){
  // a jump or a fling delivers SEVERAL entries in one batch, NOT ordered by time. Taking whichever
  // intersecting entry comes last can commit a section the reader has already passed.
  var pick = null;
  for(var j=0;j<ents.length;j++){ if(!ents[j].isIntersecting) continue;
    if(!pick || ents[j].time > pick.time) pick = ents[j]; }
  if(pick) activate(idx.get(pick.target));
}, {rootMargin:"-50% 0px -50% 0px", threshold:0});      // a zero-height centre line
var cardIO = new IntersectionObserver(/* toggle .in */, {rootMargin:"-20% 0px -20% 0px", threshold:0});
```

**Debounce the scene commit.** `activate()` updates the rail immediately but waits ~140 ms before calling
`enter()`. Scrolling *past* a beat must not kick off its camera animation; only the beat you settle on
commits. This is what kills reverse-scroll hangs, where a deep `easeTo` fires on every beat passed through.

**Keep the scroll handler O(1).** A progress bar or a hint toggle is fine; cache `scrollHeight` at boot
and on resize, because reading it per frame forces the layout this design exists to avoid. Cache each
section's `.card` once rather than calling `querySelector` per callback.

**The render loop needs three gates**, none of which changes what is drawn: skip on `document.hidden`;
skip while a scroll gesture is in flight (the map is fixed and stationary, so the last frame is still
correct, and camera eases keep drawing through the map's own `render` event); and cap ambient redraw at
about 33 fps. Without them the overlay repaints the full viewport at 60 fps for as long as any geo beat
is on screen, permanently competing with the scroll.

Boot: build rail dots from `sections`, then observe. A `window.__APP = {map, state, PHASES}` handle is
worth exposing as a console debugger for stuck beats. Frame budgets and canvas costs: `performance.md`.

## The three wire-points (memorise)

Adding beat `X` = (a) a `<section data-step="X">` card + (b) a `PHASES.X` spec + (c) the flags acted on in
`enter()`/`draw()`. Miss (b) and the beat flies nowhere; miss (c) and it renders blank. After any change, grep
every `data-step` in the HTML against the `PHASES` keys and the `draw()` flag checks — a mismatch is a silent
blank beat.
