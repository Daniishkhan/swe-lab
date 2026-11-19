# swe-lab: how to work in this repo

A local study book for senior software engineer interviews (Netflix / Anthropic
bar). Danish reads the chapters and writes every exercise solution. Claude
writes chapters, teaches, coaches and runs mock interviews. Plain HTML/CSS/JS,
opened straight from disk (`file://`), no build step except `tools/build.py`.

## Hard rules

1. **Never write exercise solutions,** not in the repo and not in chat. Stubs
   `raise NotImplementedError`. To verify tests, put reference solutions in a
   scratch folder outside the repo, run `tools/check_exercise.py`, then delete
   them. Pen-and-paper warm-up answers in a collapsed aside are fine.
2. **Every chapter is a book chapter.** Spec: `templates/README.md`. Reference:
   `sections/02-algorithms/concepts/sorting.html` and `complexity.html`. The
   other chapter 1 and 2 pages are older "box" pages waiting to be rewritten.
3. **No external dependencies in pages.** No CDNs, frameworks or `fetch()`;
   everything works offline from `file://`. Use `assets/viz.js`.
4. **No hard-coded colors.** Use the Ayu theme tokens from the top of
   `assets/style.css` (`var(--accent)`, `--ok`, `--warn`, `--bad`,
   `--accent-2`, `--brand`…) so Ayu Dark, Mirage and Light all work.
   `shell.js` colors Python code blocks; give any other `<pre>`
   `class="diagram"` or `class="plain"`.
5. **Exercise module names are unique repo-wide** (pytest imports them by
   bare name; there are no `__init__.py` files).
6. After adding or renaming a page or exercise, run `python3 tools/build.py`
   and commit the regenerated `assets/curriculum.js`.

## Skills (`.claude/skills/`)

| When | Skill |
|---|---|
| Danish wants to understand a topic, or be quizzed on one | `teach` |
| Danish is stuck on an exercise, or wants a solution reviewed | `coach` |
| A practice interview | `mock-interview` |
| Writing or rewriting a chapter | `write-chapter` → `visuals-and-layout` → `review-chapter`, repeating the review until it comes back clean |

## Commands

```bash
python3 -m pytest -k <name>                         # one exercise's tests
python3 tools/build.py                              # regenerate assets/curriculum.js
python3 tools/new.py concept 03.01 slug "Title"     # also: exercise, case, story, lld
python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py   # prove the tests work
node tools/check_page.js <page.html> [--shots DIR]  # console errors, offline, 390px scroll, markup
```

## Layout

- `curriculum.json`: source of truth for sections and topics (ids like `02.02`,
  tags P0/P1/P2).
- `sections/NN-slug/concepts/*.html`: chapters, each with
  `<meta name="topic" content="NN.MM">`.
- `sections/NN-slug/exercises/name.py` + `test_name.py`: stub and tests. The
  stub's docstring has a `Topic: NN.MM` line.
- `sections/15-interview-formats/mock-log.md`: one row per mock interview.
- `assets/`: `style.css` (theme tokens, book styles), `shell.js` (top bar,
  sidebar, theme switch, code colors), `book.js` (quick checks, review),
  `viz.js` (`V.el`, `V.s`, `V.cells`, `V.player`, `V.binaryTree`, `V.graph`),
  `app.js`, `curriculum.js` (generated).
- `templates/`: page and exercise skeletons, worksheets, and the style guide.
