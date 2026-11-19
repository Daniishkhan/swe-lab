# swe-prep: how to work in this repo

A local study book for senior software engineer interviews (Netflix / Anthropic
bar). Danish reads the chapters and solves the exercises himself. Plain
HTML/CSS/JS, opened straight from disk (`file://`), no build step except
`tools/build.py`.

## Hard rules

1. **Never write solutions into the repo.** Exercise files are stubs that
   `raise NotImplementedError`. Verify tests with reference solutions in a
   scratch folder outside the repo, then delete them. Don't put answers to the
   coding exercises in pages either (pen-and-paper warm-up answers in a
   collapsed aside are fine).
2. **Every chapter is a book chapter** (format below). The older "box" pages in
   chapter 1 and chapter 2 are being rewritten into this format.
3. **No external dependencies in pages.** No CDNs, no frameworks, no fetch().
   Everything must work offline from `file://`. Use `assets/viz.js` helpers.
4. Exercise module names must be **unique across the whole repo** (pytest
   imports them by bare name; there are no `__init__.py` files).
5. After adding or renaming a page or exercise, run `python3 tools/build.py`
   (it regenerates `assets/curriculum.js`). Commit the regenerated file.

## Writing a chapter: the pipeline

Use the skills in `skills/` in this order (read each `skills/<name>/SKILL.md`
and follow it). Each one is a separate pass; don't skip the reviews. To also
register them as Claude Code slash commands, run once from the repo root:
`mkdir -p .claude && cp -R skills .claude/` (re-run after editing a skill).

1. `write-chapter`: draft the chapter and its exercises.
2. `plan-visuals`: decide where a visualization teaches better than words, and
   build those.
3. `design-layout`: check the page as a reader sees it (desktop and phone).
4. `review-chapter`: adversarial review for correctness, clarity and gaps.
   Fix what it finds, then re-run it until it comes back clean.
5. Verify: tests pass against scratch reference solutions and fail against the
   stubs; `tools/build.py` runs; page loads with no console errors and no
   sideways scroll at 390px wide.

## The book format (summary)

Reference chapters: `sections/02-algorithms/concepts/complexity.html` and
`sorting.html`. Full spec: `templates/README.md` ("Book chapters").

- Reads top to bottom like a book: problem story → numbered sections that each
  build on the last → interview script → summary → review → exercises.
- Voice: explain it to a smart high schooler. Short sentences, everyday
  pictures, real numbers. Define each term the first time. No jargon walls.
- Spend the most words on the hardest ideas. Easy ideas get a paragraph.
- Each section: plain explanation → picture/figure → `.keyidea` → `.check`.
- Quick checks are the "adaptive" part: the wrong-answer feedback explains the
  idea **again, a different way**, not just "the answer is B".
- Optional depth goes in `details.aside.deeper`; a second analogy goes in
  `details.aside.another`.
- Exercises: `warm` (paper), `core` (code, with tests that *measure work*:
  count comparisons/reads/copies, so a correct but slow answer fails),
  `stretch` (design, measure, or "say it out loud").

## Look and feel: Ayu

The site uses the Ayu color theme: **Ayu Dark** by default, with **Ayu Mirage**
and **Ayu Light** on the theme button (or press `t`). All colors are CSS
variables defined once per theme at the top of `assets/style.css`; never
hard-code a color in a page or a visualization, use `var(--accent)`,
`var(--ok)`, `var(--warn)`, `var(--bad)`, `var(--accent-2)`, `var(--brand)`
and friends so all three themes work. `shell.js` colors Python code blocks
with Ayu's syntax colors automatically (`--syn-*` tokens); add
`class="diagram"` or `class="plain"` to a `<pre>` that isn't Python.

## Layout of the repo

- `curriculum.json`: source of truth for sections and topics (ids like `02.02`,
  tags P0/P1/P2).
- `sections/NN-slug/concepts/*.html`: chapters, each with
  `<meta name="topic" content="NN.MM">`.
- `sections/NN-slug/exercises/name.py` + `test_name.py`: stubs and tests. The
  stub's docstring has a `Topic: NN.MM` line.
- `assets/`: `style.css` (Ayu theme tokens, book styles), `shell.js` (top bar,
  sidebar, TOC, theme switch, code colors), `book.js` (quick checks, review, progress bar), `viz.js`
  (`V.el`, `V.s`, `V.cells`, `V.player`, `V.binaryTree`, `V.graph`), `app.js`.
- `skills/`: the chapter pipeline (write, visuals, layout, review).
- `tools/new.py`: scaffold pages and exercises. `tools/build.py`: index.
- Run tests: `python3 -m pytest -k <name>`. Open the book: `open index.html`.
