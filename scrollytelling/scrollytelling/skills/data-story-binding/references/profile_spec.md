# Profile spec

What `scripts/profile.py <dir>` emits, and how to read it. The profile is the **only** thing read after
this step; the raw folder is never opened again. Target size: under about 8 KB.

## Top level

```yaml
root: <dir>
generated: <iso8601>
total_bytes: <int>          # whole folder, so the size gap to the deck is explicit
file_count: <int>
files:
  - ...                     # one entry per file, below
warnings:
  - "buildings.geojson is 500 MB; hard-refuse embedding raw (sample or aggregate first)"
```

## Per file

```yaml
- path: relative/path.xlsx
  id: 9f3a1c2b                # sha256[:8] of contents, for the cache
  bytes: 39391
  kind: xlsx | csv | geojson | gpkg | parquet | json | other
  vintage: 2025-Q1 | unknown  # unknown vintage caps derived figures at grade B
  # tabular (csv / xlsx sheet / parquet):
  rows: 4255
  sheets: [Spend, Verification]   # xlsx only
  columns:
    - name: units_total
      dtype: int
      null_pct: 0.0
      distinct: 283
      role: measure | key | label | geo | time   # a guess
      unit: count | m2 | currency | pct | none    # a guess
      samples: [3, 5, 12]                          # 3-5 values, never the full column
      formula: "=SUM(B2:B14)"                      # xlsx only, the cheapest provenance signal
  # geo (geojson / gpkg):
  geometry: Polygon | Point | LineString
  features: 48
  crs: "EPSG:4326 (declared)" | "EPSG:4326 (assumed, no .prj)"
  bbox: [minx, miny, maxx, maxy]
  validity_pct: 100.0         # share of geometries that pass is_valid
  coord_precision: 6          # decimal places, hints at real resolution
  sensitive: false            # true if shaped like raw movement (id + fine timestamp + lat/lon)
```

## Fields that carry weight

- **`formula`** — the fastest way to learn which figures are derived and from what. A cell that is
  `=SUM(...)` is a candidate `sum_equals` invariant; a cell that is a hardcoded literal in a "computed"
  column is a red flag.
- **`role` / `unit`** — guesses, not truth. They seed the argue and invariant steps; confirm before
  binding.
- **`crs` declared vs assumed** — never silently assume a projection. An assumed CRS caps geo-derived
  figures and must be resolved before any area or distance is computed.
- **`sensitive`** — gates the privacy rules. A `sensitive: true` file must never be embedded per-record;
  aggregate to a k-anonymity floor first.
- **`vintage: unknown`** — caps any figure derived from that file at grade B, because you cannot vouch for
  freshness.

## Candidate keys and joins

```yaml
candidate_keys: [ncc_id, cluster_id]       # columns that are unique or near-unique
candidate_joins:                            # name + sampled-value overlap across files
  - {left: plots.ncc_id, right: mix.ncc_id, overlap: 0.98}
```

These seed the driver/relationship walk without opening the data again.
