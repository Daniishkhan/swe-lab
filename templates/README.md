# Templates and house style

`python3 tools/new.py ...` copies these files into the right chapter and fills
in the placeholders (`concept.html` is the book chapter skeleton). This page is
the style guide that keeps new pages consistent.

## Book chapters (the new format, use this for rewrites)

`sections/02-algorithms/concepts/complexity.html` and `sorting.html` are the
reference. A book chapter reads top to bottom instead of being a stack of boxes:

- `<main class="content book">`, load `assets/book.js` after `shell.js`.
- `header.chapter-head` (eyebrow, plain-English h1, meta), intro, and a
  `.learn-list` of plain-English outcomes (**zero unintroduced jargon or
  Big-O walls** before Section 1).
- The "How to read this" line names the chapters this one builds on. They are
  the topic's `requires` in `curriculum.json`.
- **Target scope:** ~2,000–3,500 visible words (~12–20 min), 6–9 numbered
  sections, 5–8 quick checks. Focus the main path on **one core mental model**;
  put secondary architectures, proofs, runtime internals, and historical/security
  deep dives in `details.aside.deeper` — or split into Part 1 (Intuition, Core
  & Patterns) and Part 2 (Under the Hood).
- **Canonical data flow:**
  1. `<h2 id="s1"><span class="sec-num">1</span>Why do we even need this?</h2>`
     — `.story` pain with real numbers + early visual before/after + quick
     preview of the 2–4 real problems it unlocks.
  2. **The rebuild (4–6 numbered sections)** — one fix per section forced by
     the previous step's flaw, with **question/tension headings** and **one
     running physical analogy** carried throughout (noting where it breaks).
  3. **How can this break?** — 2–4 core gotchas, worst case, and when it is the
     *wrong* tool.
  4. **How you use this in interviews** — concrete patterns with before/after
     examples (never a tiny afterthought table).
  5. **What to say in the interview** — a 3–5 step spoken script.
  6. `#summary`, `<div class="review" id="review">`, `#exercises` (`.exercise`
     cards tiered `warm`, `core` with work-measuring tests, `stretch`), and
     `nav.chapter-nav`. Point its links at the section neighbours; on track
     pages `shell.js` rewrites them to follow the track.
- **Inside each section (strictly intuition before formalism):**
  1–2 sentences raising the question → physical picture (running analogy and/or
  visual) → small mental-math numbers (3–8 items) → plain-English rule *then*
  its CS name/symbol → 5–15 lines of commented Python if needed → `.keyidea` →
  `.check`. Hard ideas get more space.
- **Visual pacing:** First visual in Section 1 or 2; never more than 2
  consecutive sections without a visual (`.figure`, inline SVG, or `.diagram` —
  plain tables and code blocks do not count).
- **Quick checks (`.check`):** `.q`, 3 buttons in `.opts` (one `data-correct`),
  `.fb.right`, and `.fb.wrong` (re-teaching from a *different* angle). Test
  mental models, predictions, and "what breaks if X changes" — never detached
  math/probability trivia or pure terminology recall.
- **Optional asides:** `details.aside.another` ("Explain it another way") and
  `details.aside.deeper` ("Go deeper") for secondary architectures, proofs, and
  senior/production internals.
- **Voice:** Warm, direct mentor talking to a smart friend — never dry
  conclusion-first textbook prose. Short sentences, one running everyday
  analogy, small head-traceable numbers. Define every term the first time it
  appears. Never "simply", "obviously" or "trivially". The full method is in
  `.claude/skills/teach/SKILL.md` and `.claude/skills/write-chapter/SKILL.md`.

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
