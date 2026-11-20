---
name: visuals-and-layout
description: Decide where a swe-lab chapter needs a visualization, build it with assets/viz.js, then check how the page reads on desktop and phone. Use after a chapter is drafted, or when a section is hard to follow in words.
---

# Visuals, then layout

Two passes over a drafted chapter: first what to show, then how it reads.

## 1. Find the spots for a visual

A visual earns its place when it shows something **changing step by step** or
**a shape you can't hold in your head**: a pointer moving, a structure growing,
work splitting into levels, two curves pulling apart. If a sentence or a small
table says it as well, don't build one.

For each candidate, write down the idea it teaches, why words struggle there,
and the kind:

- **Stepper** (`V.player` with frames): an algorithm's mechanism.
- **Slider**: input → live numbers or chart, for growth and trade-offs.
- **Playground**: pick algorithm × input shape, for comparisons.
- **Static diagram**: `pre.diagram` or inline SVG.

Most chapters need 2–4: one stepper for the core mechanism, one slider or
playground for "how does it scale, when does it break". Each sits right after
the paragraph that raises its question.

## 2. Build them

- `assets/viz.js` only (no libraries): `V.player(box, {frames, draw, speed})`,
  `V.cells(values, {cls, ptrs, idx})`, `V.binaryTree`, `V.graph`, `V.el`, `V.s`.
- Cell states mean the same thing in every chapter: `cmp` being compared,
  `hl` just written or current, `done`/`win` finished or in the window,
  `pivot`, `dim`, `bad`, `warn`.
- Every frame's `msg` says what just happened and why, with the actual values:
  "5 < 8, so 5 goes down."
- Wrap each in `<div class="figure">` with a `.cap` that says what to look at
  and what to try: "Press Double n and watch the ratio."
- Small inputs (5–30 items). Show the counts and compare them with the
  formula at the end.
- Colors only through theme tokens (`var(--accent)` and friends), so Ayu Dark,
  Ayu Mirage, Gruvbox Dark Hard and Ayu Light all work.
- One IIFE per figure in the script at the bottom of the page.

## 3. Check the layout

Run `node tools/check_page.js <page> --shots <scratch dir>` and look at the
screenshots (desktop 1280 wide and phone 390 wide, every theme). Then check:

- **Rhythm:** no more than about 4 paragraphs in a row without code, a figure,
  a key idea, a check or a table.
- **Order in a section:** the words that raise the question come before the
  figure or code that answers it. Then `.keyidea`, then `.check`.
- **Code:** at most about 15 lines, beside the prose that explains it.
  Side-by-side comparisons use `.cols`, which stacks on a phone.
- **Figures:** controls fit on one line on desktop and wrap cleanly on a phone.
- **Tables:** inside `.table-wrap`, so on a phone they scroll in their box,
  not the page.
- **Asides:** right after the idea they extend, closed by default, with a
  summary that says what's inside.
- **Outline:** h2 numbered sections, h3 only for sub-steps; the sidebar
  table of contents reads as a sensible outline on its own.
- **Consistency:** same classes and patterns as the reference chapters. A new
  pattern goes in `assets/style.css` (Book chapters block) and in
  `templates/README.md`.

Fix what you find, re-run the script, and report the changes by section id
("s4: moved the partition figure above the code that refers to it").
