---
name: plan-visuals
description: Decide where a swe-prep chapter needs a visualization and build it with assets/viz.js. Use after drafting a chapter or when a section is hard to follow in words.
---

# Plan and build visualizations

A visualization earns its place when it shows something **changing over time**
or **a shape you can't hold in your head**: a pointer moving, a structure
growing, work splitting into levels, two curves pulling apart. If a sentence or
a small table says it just as well, don't build one.

## Find the spots

Read the chapter and list each candidate with:
- The idea it teaches, in one sentence.
- Why words alone struggle there (state changes step by step? comparing growth?
  a tree/graph shape?).
- The kind: **stepper** (`V.player` with frames, for algorithms), **slider**
  (input → live numbers/chart, for growth and trade-offs), **playground**
  (pick algorithm × input shape, for comparing), or **static diagram**
  (`pre.diagram` or inline SVG).

Good defaults: one stepper for the core mechanism, one slider or playground for
the "how does it scale / when does it break" question. Most chapters need 2–4.
Each must answer a question the reader is actually asking at that point in the
text, and sit right after the paragraph that raises it.

## Build rules

- Use `assets/viz.js` only: `V.player(box, {frames, draw, speed})` where each
  frame has a `msg` caption (HTML allowed); `V.cells(values, {cls, ptrs, idx})`
  for arrays; `V.binaryTree`, `V.graph`, `V.el`, `V.s` for the rest.
- Cell states: `cmp` (being compared, yellow), `hl` (just written, blue),
  `done`/`win` (finished, green), `pivot` (purple), `dim`, `bad`, `warn`.
  Keep these meanings consistent across chapters.
- Every frame's `msg` says **what just happened and why**, in plain words, with
  the actual values ("5 < 8, so 5 goes down").
- Wrap it in `<div class="figure">` with a `.cap` that tells the reader what to
  look at and what to try ("Press Double n and watch the ratio").
- Keep inputs small (5–30 items) so each step is readable. Show the counts
  (comparisons, steps) and compare them with the formula at the end.
- Use theme tokens (`var(--accent)` etc.), never hard-coded colors, so light and
  dark both work. No external libraries.
- Put the script at the bottom of the page in one IIFE per figure.

## Verify

Load the page headless (Playwright), click through each player to the last
frame, and check: no console errors, captions make sense at every step, and no
sideways scroll at 390px wide.
