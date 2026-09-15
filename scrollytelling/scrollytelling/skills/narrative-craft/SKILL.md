---
name: narrative-craft
description: Write the story of a data deck — the arc, the per-beat copy, the pivot words, and the linking between beats — so it reads as one argument, not a slideshow. Use when drafting or revising the narrative and copy of a scroll-driven deck, report, or any beat-by-beat data story.
---

# narrative-craft

The words and their order. A data deck is an *argument*: state a claim, earn it through one grounded
example, land it again. This skill owns the arc, the per-beat copy, and the linking that carries a reader
from one beat to the next without a gap. It is project-agnostic; a project's brief, chosen arc, and
on-screen glossary live in `references/project/`.

Get the arc right on paper before any code. Revising framing in a beat list costs almost nothing;
revising it inside a built artifact is the most expensive place to discover you asked the wrong question.

## The spine: state → prove → restate

State the headline early, prove it step by step through one grounded, named example, then restate the
**exact same number** at the end, now earned. Repetition of one figure, once claimed and once proven, is
the rhetorical engine. Carry the number forward verbatim: same token, never paraphrased or re-rounded.
The hook number and the close number must mirror each other.

## Every deliverable has a start, a development and an end

This holds for a deck, a one-page memo, a report and a findings page alike. A pile of true statements in
a sensible order is not a story, and it is what a draft defaults to.

- **Start.** Establish the situation and the tension in the first beat: what was believed, and what does
  not fit. A reader who cannot say what is at stake after the opening will not follow the middle.
- **Development.** One movement per beat, each changing what the reader knows. The test is the
  read-through below: if two consecutive beats answer "what did I learn?" the same way, they are one
  beat. This is where the evidence lives, and it must escalate rather than accumulate.
- **End.** Land the opening claim, now earned, in the same words. An ending is not a summary and not a
  next-steps list. If the last beat could be deleted without loss, the deck stopped instead of ending.

**A storyline is carried by the writing, not by labels.** The arc has to be felt in how one beat hands
over to the next; stamping "ACT II" on a section does not create a turn, it announces one that either
exists or does not. Prefer a connective sentence that names what just changed and what it forces next.
Reach for explicit dividers, numbered eyebrows or a progress rail only where the work genuinely moves
through named stages and the reader needs to know which one they are in. Number a sequence, name a set:
a reader who sees "03" expects 02 to have caused it.

**The shape is checkable before any code.** Write the three sentences (situation, turn, landing) and see
whether the beat list actually delivers them. Fixing the arc costs a line in a storyboard and a rebuild
in an artifact.

## Choosing the arc

- **answer-first** when the audience is a repeat, time-constrained decision-maker and the number *is* the
  deliverable. Lead with the answer, then support it. See `references/arcs/answer-first.md`.
- **build-to-verdict** when the finding is counterintuitive or the *method* is the sell. Withhold the
  verdict, walk the evidence, arrive. See `references/arcs/build-to-verdict.md`.
- The house default is a six-act shape (hook, tour, pivot, method, aggregation, close), which is a
  build-to-verdict variant. See `references/arcs/six-act.md`.

The arc is not derivable from the data alone; it depends on the audience and whether the finding is
expected. Propose it, let a human confirm it, then draft.

## Per-beat template

Each beat carries **exactly one idea**:

- **eyebrow** — a short uppercase kicker, numbered within its act, e.g. `"The methodology · 03 · Signals"`.
  Numbering signals progress.
- **headline** — one short line, one `<em>` on the pivot word. Declarative, plain, confident, no hedging.
- **body** — one to two sentences. One claim. Plain English, no marketing gloss.
- **one card component** — a stat row, or bars, or a table, or a lede. Do not stack several.
- **one map / canvas scene** — the camera target plus which layers animate (owned by the engine skill).

**Eyebrows are breadcrumbs**: `<Act> · <facet>` inside a named sequence; a short noun phrase when
standalone; bare on act dividers. A reader who glances only at eyebrows should still track where they are.

## Pivot-word tests (all three must pass)

The one italicised word is the qualitative turn of the beat, not decoration.

- **Deletion**: if the headline is still fully informative with the word removed, it is the wrong word.
- **Not-the-subject, not-the-number**: the eyebrow already names the subject and the digits are already
  emphasised; the pivot is neither of those repeated, it is the turn.
- **Uniqueness**: with the pivot restored, the headline must fit *this* beat only, not its neighbours.

## Connectedness (the linking)

A deck reads as one argument only if each beat visibly hooks the last:

- **Name the literal colour** rather than forcing a legend lookup: "coloured stays inside, grey leaks out."
- **Name the delta** from the previous beat: what changed, by how much, since the beat before.
- **Carry numbers forward verbatim.** A figure introduced in beat 2 reappears in beat 20 as the same token.
- **Demonstratives resolve in-beat.** Every "this" / "here" / named colour must point at a layer actually
  rendered in that same beat. Reordering a beat otherwise orphans a "this".

## Anti-slop

Write well on the first pass; do not rely on a linter to fix bad prose.

- Bad drafts **explain, justify, and imply** in one sentence. Good copy states **one claim**. Justification
  belongs in a `.note` aside, never stacked as a second clause on the claim sentence.
- **Banned in visible copy:** em dashes (use a colon, comma, or period); hedges that dodge commitment;
  throat-clearing openers ("Let's look at", "It's worth noting"); rhetorical questions; "X and also Y";
  AI tells ("dive into", "unpack", "leverage", "seamless", "holistic", "in today's landscape"); passive
  voice hiding a knowable actor.

## Read-through protocol

Read eyebrow + headline + body in order, top to bottom. Per beat, answer: *what did I learn that I did not
know one beat ago?* Two identical answers means merge or cut. The final beat's answer must equal the first
beat's claim, now proven.

Then read only the first beat, the middle one and the last. Those three alone must carry the situation, the
turn and the landing. If they do not, the deck has no arc and reordering beats will not give it one.

## Word budgets (house default, override per project)

Eyebrow ≤7 words · headline ≤7 words with exactly one `<em>` · body ≤2 sentences and ≤40 words. These are
convention from the house's own decks, not a researched constant. Treat a breach as a warning, not a
failure; a taste rule that blocks a deadline gets the whole practice abandoned.

## References

- `references/arcs/` — answer-first, build-to-verdict, and the six-act house arc, each with a beat skeleton.
- `references/craft_examples.md` — good/bad copy pairs and the pivot-word worked example, neutral domain.
- `references/project/` — this project's brief, chosen arc, on-screen glossary, banned-figure list.
