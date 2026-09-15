---
name: data-story-binding
description: Turn a data folder into sourced, graded, contract-bound numbers that never drift on screen — profile a large folder cheaply, grade every figure, bind each to one registry, and keep prose and charts in sync. Use for any data-driven HTML deck, dashboard, or report where a figure appears in more than one place and must stay consistent and sourced.
---

# data-story-binding

Every number a reader sees is data, not text. This skill covers the whole path from a raw data folder to
on-screen figures that cannot drift: profile the folder cheaply, argue the headline, grade each figure,
bind it to one registry, and keep the prose and the charts computing from the same source. Project-agnostic;
a project's source files, profile, and contract live in `references/project/`.

## 1. Profile before you read

A data folder is often gigabytes against a deck of a few megabytes. You physically cannot read the folder,
and you must never keep a raw data file's contents in context. Build a compact **profile** first and read
only that.

- Run `scripts/profile.py <dir>` (or reproduce its logic): walk every file once, cache by
  `sha256[:8]` + mtime, emit a profile under about 8 KB. Per column: dtype, null rate, distinct count, a
  role guess, a unit guess, 3-5 samples (never a full column). For spreadsheets, **capture the formula
  string** — the cheapest way to learn which figures are derived and from what. For geo: geometry type,
  feature count, CRS (declared vs assumed), bounding box, validity percentage, coordinate precision.
- Flag `sensitive: true` on anything shaped like raw movement (an id plus a high-frequency timestamp plus
  lat/lon). See `references/profile_spec.md` for the full shape.
- Hard-refuse embedding any raw source over 2 MB into the artifact. Large sources get sampled or aggregated
  first, never inlined whole.

## 2. Argue the headline by score, not vibes

Pick the headline number by a rule you can show:

- named in the brief **+3**
- structural centrality (other columns or sheets sum into it, visible in captured formulas) **+2**
- independently produced by two sources **+2**
- passes its own invariant, e.g. shares sum to 100 **+1**

A contradiction between sources disqualifies a candidate from headline. A figure with only an assumed grade
is capped at footnote. Present the winning headline **with the runners-up and the specific reason each one
lost** — do not let an assumed figure become headline by omission.

## 3. Grade every figure

Grades, defined once (see `references/grades.md`):

- **A measured** — read from a named cell/column or an authoritative cited stat.
- **B derived** — a documented formula over contract keys; B even if all inputs are A, because formulas can
  be wrong.
- **C assumed** — any unsourced coefficient or extrapolation; must render with a visible marker on screen.

Propagation: a derived figure inherits the **worst** grade among its inputs (`min`), with one further
downgrade if any input is an unsourced assumption. Surface the grade next to the number so a weak input is
never laundered into a confident-looking total.

## 4. Bind, do not type

- **One registry.** All numbers in a single data object: a `metrics` map (id → value, source, grade) and a
  `series` map (id → array). Nothing on screen holds a literal.
- **Bind by attribute.** Each on-screen figure is a placeholder carrying its registry id (e.g.
  `data-bind="wallet_total"`). A `hydrate()` pass at load fills every placeholder from the registry.
- **Builders for derived views.** Anything computed (a sum, a share, a per-capita line) is produced by a
  small builder that reads registry inputs and writes DOM. Derived numbers are recomputed, never typed, so
  they cannot drift from their inputs.
- **Re-entry guard.** Each builder checks its target is empty first (`if (!el || el.childElementCount)
  return;`) so re-running hydrate is safe.
- **Display rounding is declared policy.** A metric may carry `display: exact | round | floor_plus | band`
  so a deck can legitimately show "30,000+" while the registry holds the exact figure. Verify the rounded
  display is *consistent with* the source; do not flag it as a mismatch.

## 5. The duplicate-key trap (learn this one)

A registry is one namespace across the whole file. This renders a beat empty with no error:

- Before adding any `metrics` or `series` key, **count it across the whole file**. If it already exists,
  reuse it and adapt your consumer to the existing shape.
- In a JS object literal, a key that appears twice: the **last one silently wins**. A consumer expecting
  the shape you injected gets the other shape, produces nothing, and throws no error. A syntax check cannot
  see it. Catch it by simulating the builder in node against the real blob and asserting non-empty output.

## 6. The sync rule (where drift hides)

When numbers change upstream, **every entry under `metrics` or `series` is in scope for the diff, full
stop, no implicit headline exception**. The most-quoted figures are exactly where a partial pass forgets to
look. After a headline rebase, recompute every derived rate, share, and percentile from the identity, and
grep the whole file for the old number rather than trusting a prior pass's partial patch.

## 7. Invariants that generalise

A small library (auto-proposable from the profile, see `references/invariants.md`): `sum_equals`,
`share_sums_to`, `range`, `monotonic`, `non_negative`, plus tolerance-banded reconciliation between two
independent estimates (≤10% converges and may be cited as validation; ≤25% report both, never silently
average; >25% blocks a two-reads claim).

## 8. Analytical guardrails (do not draw the wrong number)

- **City is not the captive community.** City-wide behaviour is an upper envelope; use it to bound and
  tighten a local estimate, never to inflate the local up to open-catchment city rates.
- **Train where there is data, infer where there is not.** When the target has no signal of its own, learn
  on the places that do and reweight to a relevant reference population, not the raw city average.
- **Attribute at the right level.** Footfall is per-agglomeration (an anchor plus its satellites), not
  per-store; a regression of visits on store-count is confounded. Use visits-per-shop plus dwell plus
  loyalty, attributed to the anchor.
- **Read the full distribution.** A floored or zero median is not "no signal"; the useful separation often
  lives above the median.
- **Benchmarks validate, they do not feed the model.** An external ratio or published density is for
  validation and direction only. Hardcoding it as a model input launders an outside assumption into your
  own result. Keep it graded and cited as a check, never as a driver.

## References

- `references/grades.md` — the A/B/C rubric, `kind` field, propagation rules.
- `references/invariants.md` — the invariant library and the reconcile bands.
- `references/profile_spec.md` — what `profile.py` emits and how to read it.
- `references/project/` — this project's source workbook/geojson, generated profile, contract.
