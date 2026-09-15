# Invariants

A small library of checks a figure must satisfy, most auto-proposable from the profile. Attach the relevant
ones to registry entries in the contract; a build-time or verify-time pass asserts them.

## The library

- **`sum_equals`** — a set of parts equals a declared total. Proposed when the profile finds a column set
  and a "Total" row/column. `{sum_equals: [part_a, part_b, part_c], total: grand_total, tolerance: 0}`
- **`share_sums_to`** — a set of shares sums to 1 (or 100). `{share_sums_to: [s1, s2, s3], target: 100}`
- **`range`** — a value stays within bounds. `{range: [0, 1]}` for a rate; `{range: [0, null]}` for a count.
- **`monotonic`** — a series only rises or only falls. `{monotonic: increasing}`
- **`non_negative`** — shorthand for `range: [0, null]`; proposed for every count and area column.
- **`reconcile`** — two independent estimates of the same quantity agree within a band (below).

## Reconciliation bands

When the same quantity is produced two ways (a top-down and a bottom-up total, say), the gap between them is
itself a finding:

```yaml
reconcile:
  - {a: topdown_total, b: bottomup_total, tolerance_pct: 10, warn_pct: 25}
```

- **≤10%** — the two reads converge; you may cite the agreement as validation.
- **≤25%** — report both numbers, never silently average them into one.
- **>25%** — blocking. A "we measured it two ways and they agree" arc cannot be used honestly; either the
  method or the data is wrong, and the deck must not claim convergence.

## Proposing invariants from the profile

The profiler's structure hints suggest invariants automatically:

- a column set beside a `Total` column → `sum_equals`.
- columns named like shares/percentages that span a group → `share_sums_to`.
- any count or area column → `non_negative`.
- a time-ordered value the brief calls a trend → `monotonic`.

Auto-proposal is a starting point, not a guarantee. Confirm each proposed invariant against what the number
actually means before binding it; a spurious `sum_equals` on columns that were never meant to total is
worse than none.
