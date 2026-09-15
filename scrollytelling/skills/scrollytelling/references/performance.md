# Performance

A scroll deck is judged on whether it feels smooth, and that is measurable from the terminal. This file
is the method, the costs worth knowing, and the traps that make a broken deck look fine.

## Measure it, do not reason about it

`scripts/frameprobe.mjs <deck.html> --launch --walk --glide`. It drives a **headed** Chrome on a debug
port with a throwaway profile and samples `requestAnimationFrame` deltas from inside the page.

- **Headless cannot answer this question and will actively mislead you.** Software raster runs a WebGL
  map at about one frame per second, so every frame budget is meaningless. Worse, headless delivers
  **zero IntersectionObserver entries**: a scroll deck reports every card as never revealed and every
  beat as never activated, which looks exactly like a broken scroll controller and is only the harness.
  Never diagnose a scroll deck from headless card state.
- A freshly launched Chrome returns an **empty `/json/list`** until a target exists. Create one
  (`PUT /json/new`) before attaching, or the first thing you see is an undefined-property error.
- Discard the first run. Cold tile fetches produce a one-off couple-hundred-millisecond frame that does
  not reproduce warm. Run it twice and believe the second.
- **Check the harness floor before reading any beat.** A browser window that is occluded, minimised or
  on another desktop is throttled, typically to 30fps, and then every beat reports about 33 ms and the
  whole deck looks uniformly slow while telling you nothing. The tell is a beat that draws nothing
  costing the same as the heaviest one. `frameprobe.mjs` measures the floor on an idle beat first and
  refuses to call anything slow relative to a throttled baseline; the same run went from "every beat
  slow at 33 ms" to a floor of 8.3 ms simply by using a window that was actually visible.

## Read percentiles, never the mean

On a 120 Hz display the median sits at 8.3 ms whether the deck is healthy or catastrophic. A deck with
ten beats running at **0.7 fps** still reported a median of 8.3 ms. The damage shows in three places:
p99, max, and the frame **count** (a four-second window that collects 4 frames instead of 450).

Localise by parking, not by scrolling: walk each beat, stop on it, sample a dozen frames. A per-beat
table turns "the deck feels slow" into a named list of beats that share one layer.

## Canvas costs worth carrying in your head

Orders of magnitude on a current laptop at a 1600x1000 viewport, dpr 2. Use them to budget a layer, not
as a benchmark to reproduce.

| what | cost |
|---|---|
| **`closePath()` per ring in one accumulated path** | **quadratic in ring count**: ~1k rings a few ms, ~4k about 40 ms, ~20k over a second, every frame |
| the same rings closed with `lineTo(first)` | ~1 ms at 20k, flat |
| `fill()` / `stroke()` of a 20k-ring path | single-digit ms |
| stroke at a sub-pixel `lineWidth` (device px) | ~6x the cost of a 1 px stroke, different AA path |
| a few tens of thousands of individual `arc` + `fill` | ~20 ms, and batching into shared paths does **not** help |
| the same marks as `fillRect` | about half |
| `map.project()` | ~0.1 µs per vertex, so ~10 ms for 100k |
| `drawImage` of a cached full-viewport canvas | free |
| `getBoundingClientRect` on a fixed element | ~0.015 ms |

**The quadratic path is the one that bites.** Accumulating thousands of polygons into ONE path and
filling it once is right, and far cheaper than thousands of `fill()` calls. Closing each ring with
`closePath()` is what costs: the path builder charges for a closed subpath in proportion to what is
already in the path. Close with an explicit `lineTo` back to the first vertex. Non-zero winding fills an
explicitly closed ring exactly as it fills a `closePath` one. `verify.py` lints for this shape.

## The ladder, in the order that pays

1. Close batched rings with `lineTo`, never `closePath`.
2. Cache projected screen coordinates **keyed on the camera transform** (centre, zoom, bearing, pitch,
   viewport). A parked camera then reprojects nothing and the cost lands only during a fly-in.
3. One path filled once, not one `fill()` per feature.
4. Gate the ambient loop: hidden tab, a scroll-quiet window, a frame cap.
5. Debounce scene commits (~140 ms) so scrolling past a beat never starts its camera fly.
6. Use IntersectionObserver, never per-frame layout reads, to decide the active beat.

## Choose against ground truth, not against instinct

The fix that looks more correct can be the worse one, and only a pixel comparison says which.

Closing rings with `lineTo` loses the mitred join where each ring closes: about 0.06% of pixels move.
The alternative that keeps the exact join is to split the layer into many smaller paths, and measured
against a single-path `closePath` rendering it lands **twenty times further away** (~1.4% of pixels),
because every chunk composites its own fill and stroke and shared edges darken. Fastest and closest were
the same option. Render both against the unmodified original and compare **whole buffers**: a checksum
that samples every nth byte will call two different renderings identical.

## What is not worth optimising

Measured, not assumed, on a real deck: `getBoundingClientRect` once per frame costs 0.015 ms, and
`backdrop-filter` on the cards never appeared in any scroll timing. Both have bad reputations. Optimise
what the probe names, and leave the rest alone rather than trading a look for nothing.

Two beats drawing tens of thousands of ambient marks at ~30 ms per frame are also fine, because the
render loop pauses during a scroll gesture: they never touch the scroll path. Check where a cost lands
before paying to remove it.

## Comments that state performance numbers

If a comment claims a cost, it must carry the date it was measured. One in a production deck claimed
"about 60 ms" for an operation that measures 9.5, and it had never been timed. An invented number in a
comment is worse than no number: the next person optimises against it.
