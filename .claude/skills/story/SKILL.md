---
name: story
description: Write the storyline and on-screen copy for the gym mood board scroll deck: the vision → floor plan → mood arc, the beat list in story/storyboard.md, eyebrows, headlines with one pivot word, short body copy, and the links between beats. Use before any HTML work and whenever beats are added, reordered or rewritten.
---

# Story

The deck argues one thing: **a gym design project is easier to understand and decide on when vision, plan
and mood are consolidated into one story.** The words and their order carry that. Work on paper
(`story/storyboard.md`) until a person approves it; revising a storyboard line is cheap, revising a built
deck is not.

Project arc and beat skeleton: `references/arc-vision-plan-mood.md`.

## Start, development, end

- **Start**: the situation and the tension. What the client imagines (the Technogym renders), and why a
  folder of pictures does not yet make a design decision.
- **Development**: one movement per beat, each changing what the reader knows. The plan grounds the
  vision in real space, area by area; the mood says how each area should feel. Escalate, do not list.
- **End**: land the opening claim in the same words, now earned. Not a summary, not a next-steps list.

Check: the first, middle and last beat read alone must carry situation, turn and landing.

## Per-beat template

| field | rule |
|---|---|
| eyebrow | short uppercase kicker naming where we are: `Vision`, `Floor plan · Level 2`, `Mood · Change rooms` |
| headline | ≤7 words, declarative, exactly one `<em>` on the pivot word |
| body | 1-2 sentences, ≤40 words, one claim |
| visual | one `PHASES` spec: none, a figure (render or plan + box group), or a grid of tagged images |
| facts | any number is a `facts.json` id, never typed |

## Pivot word (all three must pass)

- **Deletion**: without the word the headline loses its point.
- **Not the subject**: the eyebrow already names the area; the pivot is the turn, not the noun.
- **Unique**: with the word, the headline fits this beat only.

## Linking beats

- Name what is on screen: the area ("the cardio line along the windows"), the material ("oak and
  travertine"), the colour of the highlight.
- "This" and "here" must point at something visible in the same beat.
- Carry a phrase or number forward verbatim when a later beat pays it off.
- The mood beat for an area follows the plan beat for that area, so the reader never has to remember.

## Copy the client writes

Revisions often arrive as finished sentences to drop in. Keep the words and the voice; change only what
the deck's rules forbid, and say what was changed and why.

- **Em dashes** are banned on screen. Replace with a colon or split the sentence. Never keep one silently.
- **Do not describe the pictures.** The images speak; the copy says what the material does and means.
- **Terms carry through**: say "wood", not "oak", once a beat has been generalised; the same word in the
  card, the storyboard and the brief.
- **No material is assigned to a level.** The building is one body; levels appear only as plan labels.
- A request to "make the text longer" means another claim or a concrete material, not padding.

## Anti-slop

- One claim per sentence; reasons go in a `.note`, not a second clause.
- Banned in visible copy: em dashes; hedges; "Let's look at", "It's worth noting"; rhetorical questions;
  "elevate", "curated", "seamless", "holistic", "dive into", "unlock", "state-of-the-art", "world-class".
- Name materials and places concretely: "walnut lockers", not "premium finishes".

## Revising a beat

- A request names a beat by its **on-screen number**, which is its position. Count sections to get the
  `data-step` id, and name the id back so a mis-count surfaces before the edit.
- Change `story/storyboard.md` in the same pass: its table row and the key-copy line under it. The board
  is the agreed running order and `verify.py` fails when it drifts from the deck.
- Removing an image from a beat is a copy change too: cut the sentence that pointed at it.
- When a change makes an earlier beat wrong (a word replaced everywhere, a point that no longer lands),
  say so and offer the follow-up rather than editing beats nobody asked about.

## Read-through

Read eyebrow + headline + body top to bottom. Per beat: *what do I know now that I did not one beat ago?*
Two identical answers: merge or cut. Word budgets are warnings, not failures.
