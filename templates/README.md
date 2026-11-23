# Templates and house style

`python3 tools/new.py ...` copies these files into the right chapter and fills
in the placeholders (`concept.html` is the book chapter skeleton). This page is
the style guide that keeps new pages consistent.

## Book chapters (the new format, use this for rewrites)

`sections/02-algorithms/concepts/complexity.html` and `sorting.html` are the
reference for the format. They were written before the writing rules below;
for the prose, follow the rules and
`sections/01-data-structures/concepts/hash-maps.html`. A book chapter reads
top to bottom instead of being a stack of boxes:

- `<main class="content book">`, load `assets/book.js` after `shell.js`.
- `header.chapter-head` (eyebrow, h1, meta), then a `.learn-list` of outcomes.
- Numbered sections: `<h2 id="s1"><span class="sec-num">1</span>Title</h2>`.
  The sidebar table of contents is built from these.
- Section 1 is always **the problem**, with real numbers, in plain words.
- Each idea, point first: one plain sentence that says what the idea is, then
  a concrete case (worked numbers, an example from real software or a
  `.figure` visualization), then the general rule and its standard name, then
  code if needed. Hard ideas get more words, not more boxes.
- Boxes interrupt the read, so each one needs a reason, and a chapter has at
  most about 20:
  - `.check` (quick check), at the end of a section, where a reader could
    predict wrong: `.q`, buttons in `.opts` (right one has `data-correct`),
    `.fb.right` and `.fb.wrong`. The wrong feedback must explain the idea
    again in a *different* way, not just give the answer.
  - `.keyidea` only for the two or three ideas the whole chapter hangs on. A
    section's first sentence already states its point.
  - `details.aside.deeper` ("Go deeper") for caveats, real systems and
    senior-level material; `details.aside.another` ("Explain it another
    way") for a second route into a hard idea.
- End: "What to say in the interview", `#summary`, `<div class="review" id="review">`,
  `#exercises` with `.exercise` cards tiered `warm` (paper), `core` (code with
  tests that count work, not just answers), `stretch`; then `nav.chapter-nav`.
  Point its links at the section neighbours; on track pages `shell.js`
  rewrites them to follow the track.
- The "How to read this" line names the chapters this one builds on. They are
  the topic's `requires` in `curriculum.json`.
- Voice and wording: the **writing rules** below. The explanation method
  itself (pain, primitives, rebuild one fix at a time) is in
  `.claude/skills/teach/SKILL.md`.

## Writing rules (every chapter)

Write for a colleague who is new to the topic: a working engineer, not a
child. `python3 tools/check_prose.py <page>` reports how a page does against
rules 1, 2, 6 and 7 and prints what to read by eye for 3, 4 and 5.

1. **Whole sentences you could read aloud.** No arithmetic, arrows or
   semicolons inside a sentence, and few brackets. Big-O and names in code
   font (`dict`, `__hash__`) are fine.
2. **Working goes in its own block:** a `pre.plain`, a table or a code block,
   followed by one sentence that says what it shows.
3. **Standard terms name things.** Every chapter title, heading and link to
   another chapter carries the term an interviewer would use ("Load factor",
   not "How full is too full"). Define a term once, then keep using that word.
4. **A section's first sentence states its point** in plain words. The
   example, numbers or figure come second.
5. **At most one everyday analogy per chapter.** Prefer an example from real
   software. After an analogy the text goes back to the real terms; the
   analogy's words never replace them.
6. **The running text is complete without the boxes.** It never points at a
   figure, check or aside ("see the figure below"), and it still makes sense
   with all of them skipped.
7. **About 6,000 words on the main path,** which is everything read top to
   bottom: not the collapsed asides or the exercises. Caveats, edge cases
   and "by the way" facts go in a "Go deeper" aside or get cut.
8. Define every term the first time it appears. Never "simply", "obviously"
   or "trivially".

What stays from before: every step has a reason, every term a definition, and
every claim a worked number.

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
four themes (Ayu Dark, Ayu Mirage, Gruvbox Dark Hard, Ayu Light). Cell and node states, with the same meaning in every chapter:
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
`lld-worksheet.md` (object-oriented design), `deep-dive.md` (past-project deep dive), `mock-log.md` (mock interview log).
