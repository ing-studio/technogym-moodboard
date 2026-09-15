# Arc: vision → plan → mood

The project default. Answer-first: the claim is stated in the opening, proven through the plan and the mood,
and restated at the close. Beat counts are a guide; specifics come from `story/brief.md`.

| # | chapter | beat | visual (PHASES) | job |
|---|---|---|---|---|
| 1 | Vision | hook | `hero`: 2-3 Technogym overview renders | what they imagine; state the claim |
| 2 | Vision | the kit | `hero` or `mood`: equipment details (kettlebell wall, dumbbell rack, treadmill row) | the machinery and finishes that define the expectation |
| 3 | Floor plan | the building | `plan`: level overview, `area: null` | where it really goes; the turn from picture to space |
| 4-n | Floor plan | area by area | `plan`: same level, `area: <id>` per beat | each area: what goes there, the one fact that matters |
| n+1 | Mood | per area | `mood`: 3-6 images tagged for that area | how that area should feel: materials, light, colour |
| … | Mood | materials | `mood`: material board, veneers, stone | the palette that ties areas together |
| last | Close | landing | `plan` overview or `hero` | restate the opening claim, now earned |

## Two orderings, pick one in the brief

- **Chapter order** (default): all plan beats, then all mood beats. Clear, mirrors the folder structure.
- **Interleaved**: plan area → its mood → next area → its mood. Better when areas feel very different
  (training floor vs change rooms); the reader never has to hold an area in memory.

## Mood tags available in the catalog

`training-floor`, `functional`, `studio`, `changing`, `wellness`, `reception`, `materials`, `details`, plus
material tags (`oak`, `walnut`, `travertine`, `plaster`, `rammed-earth`, …). Query `assets/catalog.json`
by tag when choosing a set.
