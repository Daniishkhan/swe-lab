# Templates and house style

`python3 tools/new.py ...` copies these files into the right chapter and fills
in the placeholders (`concept.html` is the book chapter skeleton). This page is
the style guide that keeps new pages consistent.

## Book chapters (the new format, use this for rewrites)

`sections/02-algorithms/concepts/complexity.html` and `sorting.html` are the
reference. A book chapter reads top to bottom instead of being a stack of boxes:

- `<main class="content book">`, load `assets/book.js` after `shell.js`.
- `header.chapter-head` (eyebrow, h1, meta), then a `.learn-list` of outcomes.
- Numbered sections: `<h2 id="s1"><span class="sec-num">1</span>Title</h2>`.
  The sidebar table of contents is built from these.
- Section 1 is always **the problem**, told as a small `.story` in plain words.
- Each idea: plain explanation, then a picture or `.figure` visualization, then
  a `.keyidea`, then a `.check` (quick check). Hard ideas get more space.
- Quick check: `.check` with `.q`, buttons in `.opts` (right one has
  `data-correct`), `.fb.right` and `.fb.wrong`. The wrong feedback must explain
  the idea again in a *different* way, not just give the answer.
- Optional asides: `details.aside.another` ("Explain it another way") and
  `details.aside.deeper` ("Go deeper") for the formal or senior-level material.
- End: "What to say in the interview", `#summary`, `<div class="review" id="review">`,
  `#exercises` with `.exercise` cards tiered `warm` (paper), `core` (code with
  tests that count work, not just answers), `stretch`; then `nav.chapter-nav`.
- Voice: write for a smart high schooler. Short sentences, everyday analogies,
  real numbers. Define every term the first time it appears. Never "simply",
  "obviously" or "trivially". The explanation method itself (pain, primitives,
  rebuild one fix at a time) is in `.claude/skills/teach/SKILL.md`.

## Older box pages (legacy)

Most chapter 1 and 2 pages are still stacks of collapsible `details.box`
panes. Don't write new pages in that format; rewrite them as book chapters.

## Visualizations

Use the helpers in `assets/viz.js` (no libraries, no build step):

- `V.player(el, { frames, draw })`: step-through player (first / prev / play / next / speed).
  Build an array of frames up front; each frame can carry a `msg` caption.
- `V.cells(values, { cls, ptrs })`: an array drawn as cells with indexes and pointer labels.
- `V.binaryTree(svg, root, { cls })`: lays out and draws `{val, left, right}` trees.
- `V.graph(svg, nodes, edges, { directed })`: node-link graph with fixed coordinates.

Colors come from the theme tokens in `assets/style.css`, so visuals work in all
three Ayu themes. Cell and node states, with the same meaning in every chapter:
`cmp` (being compared), `hl` (current or just written), `done` (final), `win`
(in the window), `pivot`, `warn` (frontier), `bad` (rejected), `dim`.

## Exercises (`exercise.py`, `test_exercise.py`)

- The docstring states the problem, requirements, target complexity, and the
  "say it out loud" questions. Keep the `Topic: XX.YY` line: the build script
  uses it to link the exercise to its topic.
- Stubs raise `NotImplementedError`. Never commit a solution in a stub you
  generate for someone else.
- Tests cover the prompt's example, empty/smallest input, duplicates,
  boundaries, and (where cheap) a randomized check against a brute force.
- Core exercise tests also **measure work** (count comparisons, reads or
  copies, as `test_sorts.py` does), so a correct but slow solution fails.
  Prove it with `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`,
  keeping both solutions outside the repo.
- Module names must be unique across the repo.

## Markdown worksheets

`design-case.md` (45-minute system design), `star-story.md` (behavioral),
`lld-worksheet.md` (object-oriented design), `mock-log.md` (mock interview log).
