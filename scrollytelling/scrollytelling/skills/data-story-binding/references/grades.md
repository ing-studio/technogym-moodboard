# Grades

One rubric for the credibility of every number on screen. Stated once so a weak input is never laundered
into a confident total.

## The three grades

- **A — measured.** Read directly from a named cell or column, or from an authoritative external stat cited
  with its source. No transformation beyond selection.
- **B — derived.** Produced by a documented formula over contract keys. B even when every input is A,
  because a formula can be wrong (wrong keys, wrong operation, a unit slip). A derived figure is never A.
- **C — assumed.** Any unsourced coefficient, extrapolation, or expert guess. Must render with a visible
  on-screen marker so a reader knows it is an assumption, not a measurement.

## The `kind` field

Each registry entry carries a `kind: measured | derived | assumed` alongside its grade. `kind: derived`
**requires** a `formula:` string naming the inputs. This keeps the grade honest: you cannot mark something
derived without saying from what.

```yaml
wallet_total:   { value: ..., grade: A, kind: measured, source: "Sheet 'Spend' cell B4" }
capture_share:  { value: ..., grade: B, kind: derived,  formula: "captured / wallet_total" }
online_leak:    { value: ..., grade: C, kind: assumed,  source: "analyst estimate, no primary" }
```

## Propagation

- A derived figure inherits the **worst** grade among its inputs: `grade = min(A,B,C over inputs)`.
- **One further downgrade** if any input is an unsourced assumption (`kind: assumed`): a B built partly on
  a C is reported as C, not B. This stops an assumption disappearing inside an otherwise-measured chain.
- The headline is not exempt. A headline that resolves to a C-grade input is a C-grade headline and belongs
  in a footnote, not a hero number.

## The marker

Grade C on screen needs a visible signal: a small superscript, a muted colour, a dotted underline, whatever
the design system provides, applied consistently. The rule is only that a reader can tell, without reading
a methods appendix, which numbers are measured and which are assumed.
