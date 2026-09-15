# Map grammar

The visual language for putting data on the dark basemap so it reads at a glance and earns belief. Covers
two things: **geo layers over the map** (polygons, geopackages, boundaries, heat) and **movement over the
map** (trips, footfall, catchment). One consistent grammar for both, so a reader who learns it on beat two
still trusts it on beat twenty.

## Geo data over the map

The data is usually GeoJSON or a geopackage exported to GeoJSON: polygons (plots, districts, catchments),
points (stores, homes, POIs), lines (roads, routes). Render it as a **layer on the Canvas glow overlay**,
synced to the basemap every frame, not as a static MapLibre fill you cannot animate.

- **Polygons**: draw the outline as a glowing stroke, fill at low alpha. A boundary reads as a fence; a
  filled polygon reads as an area of demand or coverage. Animate the stroke drawing on (a dash offset
  sweeping) so the shape *arrives* rather than snapping in.
- **Choropleth / heat over polygons**: bind fill alpha or hue to one measure per polygon, from the data
  registry, never hand-picked per shape. Keep the scale legible: 3-5 steps, not a continuous gradient no
  one can read. Defer the exact palette to the `dataviz` skill's sequential scale.
- **Points**: cull off-screen first, then draw as additive glow sprites. Size or brightness may carry a
  measure; keep it one measure, consistently.
- **Projection**: the overlay syncs via `map.project()` every render frame; geometry stays in EPSG:4326
  and MapLibre handles the screen transform. Screen coordinates may be **cached, but only keyed on the
  camera transform** (centre, zoom, bearing, pitch, viewport size): a stale cache drifts on zoom, a
  transform-keyed one cannot, and it is what makes a hundred-thousand-vertex layer affordable, since a
  parked camera then reprojects nothing.
- **Thousands of polygons go into ONE path**, filled once and stroked once, not one `fill()` per
  feature. Close each ring with an explicit `lineTo` back to its first vertex, **never `closePath()`**:
  path building is quadratic in the number of closed subpaths, so a 20k-polygon fabric costs over a
  second a frame with `closePath` and about a millisecond without it. `performance.md` has the numbers
  and the pixel cost of the trade.

## Core movement motif: follow the people

- **Home to road to shop.** Animate origins lighting up, flowing along the **real network path** (routed
  roads, not a straight line), arriving, and dwelling. Straight-line arrows read as abstraction; a routed
  path reads as truth.
- **One concrete trip beats aggregate arrows.** A single, named, timestamped journey (a real origin, a
  real time, a real destination) makes the method believable in a way a heat blur never does. Show the one,
  then generalise. (Privacy: a "one real journey" beat uses a seeded synthetic trip unless a specific trace
  is explicitly signed off.)

## Vocabulary (each visual carries one idea)

- **Dwell** = multi-phase ripples at the destination (arrive, settle, linger).
- **Near vs far demand** = distance bands, so the split between local and travelled-in is visible.
- **Frequency** = home-loop repeats (the same trip pulsing again).
- **Retention** = shown against the real nearby competitors it is measured against (strips or markers), not
  an abstract percentage floating on the map.
- **Capture** = isochrones for reach, comet or flare trails for inbound trips, a sieve or funnel for what
  the site keeps, then a roll-up to the wider area.

## Palette is load-bearing

Colour carries meaning; fix it once and reuse it across the whole body of work. A minimal, consistent set:

- one hue for **kept / internal** demand,
- one for **far / reach** (travelled-in, service radius),
- one for the **external corridor**,
- one for the **anchor / destination**,
- a neutral grey for what **leaked away**.

Never recolour per figure. Never encode a fact by colour alone (a colour-blind reader must still get it
from position, label, or shape). Align these hues with the `dataviz` categorical palette so chart marks and
map marks agree.

## Camera motion

- One meaningful move per beat at most. A camera that moves every beat exhausts the reader and hides which
  move mattered.
- Consecutive beats that declare the same framing must **not** re-issue a move; hold the frame and let only
  the layers or the text change. (This is the "static unless explicitly told to move" rule.)
- Ease, do not cut. A hard jump between distant framings loses the reader's spatial thread.

## Scope discipline

- Draw external corridor or pass-through catchment **only at the node that actually has it** (a regional or
  anchor node on a through-route). A resident fabric stays internal.
- Do not paint corridor flows across a whole community when only one node draws from outside. Overreach here
  is the fastest way to lose a reviewer's trust.

## Technique (generalises across every layer)

- **Additive glow** for flow and particle layers on a **dark** ground (composite `lighter`); reset to
  `source-over` for text labels. Cache one radial-gradient sprite per RGB. On a **light** ground use
  `source-over` throughout: additive compositing cannot darken, so every mark disappears. The build-up
  behaviour the density layers rely on (repeated low-alpha draws converging on the mark colour) survives
  the switch; the glow does not, and a light deck carries weight and edge instead.
- **Seeded RNG** (`mulberry32`) for every random placement so frames are deterministic and rebuilds are
  stable; never `Math.random()`.
- **Cull off-screen points** before drawing; sync the overlay to the basemap on every render frame so glow
  and basemap never drift apart.
