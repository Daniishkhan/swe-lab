# swe-lab: how to work in this repo

A local study book for senior software engineer interviews (Netflix / Anthropic
bar). Danish reads the chapters and writes every exercise solution. Claude
writes chapters, teaches, coaches and runs mock interviews. Plain HTML/CSS/JS,
opened straight from disk (`file://`), no build step except `tools/build.py`.

## How we teach (every chapter, every explanation)

Danish learns through **"why should I care?"**, **visual intuition**,
**everyday analogies**, and **first principles**. Break each topic down and
rebuild it from scratch, intuition before formalism:

1. **Start from "why should I care?" (pain + payoff):** open with a concrete
   problem with real numbers *and* a quick preview of the superpower this
   unlocks in real software and interviews — never a definition, formula, or
   Big-O wall. Keep titles, intros, and learning outcomes in plain English
   (zero unintroduced jargon).
2. **One running physical analogy:** pick a single everyday mental model
   (coat-check room, playing cards, line at a counter, filing cabinet) and
   carry it through the whole rebuild, mapping every mechanism onto it — and
   explicitly stating where the analogy breaks.
3. **Rebuild one question at a time:** break the idea down to facts a smart
   high schooler already trusts (counting, halving, waiting in line, distance
   and time), then rebuild via `Question → Naive attempt → Break → Fix`. Frame
   headings and openers as questions or tension, never dry textbook thesis
   statements.
4. **Picture first, simple numbers next, jargon last, code last:** every idea
   gets a visual or physical picture *before* formulas, symbols, Big-O, or
   code. Start with numbers small enough to trace in your head; explain the
   plain-English idea before naming the CS term (e.g., "crowdedness" before
   "load factor α").
5. **Protect the first-pass core path:** keep a chapter focused on **one core
   mental model** (~2,000–3,500 visible words, ~12–20 minutes). Put secondary
   architectures (e.g., open addressing alongside chaining), heavy math/proofs,
   language internals, and production/security edge cases in collapsed
   `details.aside.deeper` boxes — or split into a Part 2 chapter — never
   blocking first-pass intuition.
6. **Check intuition, not trivia:** check by explaining back or predicting what
   breaks when one condition changes — never "does that make sense?" and never
   detached math/probability trivia.

Write in a warm, direct mentor voice (never dry textbook prose). Short
sentences, every term defined the first time, the most words on the hardest
ideas. The full method is the `teach` skill. Chapters apply it through
`write-chapter`, `visuals-and-layout`, and `review-chapter`.

## Hard rules

1. **Never write exercise solutions,** not in the repo and not in chat. Stubs
   `raise NotImplementedError`. To verify tests, put reference solutions in a
   scratch folder outside the repo, run `tools/check_exercise.py`, then delete
   them. Pen-and-paper warm-up answers in a collapsed aside are fine.
2. **Every chapter is a book chapter.** Spec: `templates/README.md`. Reference:
   `sections/01-data-structures/concepts/hash-maps.html`.
3. **No external dependencies in pages.** No CDNs, frameworks or `fetch()`;
   everything works offline from `file://`. Use `assets/viz.js`.
4. **No hard-coded colors.** Use the theme tokens from the top of
   `assets/style.css` (`var(--accent)`, `--ok`, `--warn`, `--bad`,
   `--accent-2`, `--brand`, `--on-accent`…) so all four themes work: Ayu
   Dark, Ayu Mirage, Gruvbox Dark Hard and Ayu Light. Fonts are bundled in
   `assets/fonts/`: use `var(--read)` for prose, `var(--ui)`, `var(--mono)`.
   `shell.js` colors Python code blocks; give any other `<pre>`
   `class="diagram"` or `class="plain"`.
5. **Exercise module names are unique repo-wide** (pytest imports them by
   bare name; there are no `__init__.py` files).
6. After adding or renaming a page or exercise, run `python3 tools/build.py`
   and commit the regenerated `assets/curriculum.js`.
7. **Keep the prerequisite order.** The `track` in `curriculum.json` is the
   learning order. A topic's `requires` lists what it builds on, and every one
   must come earlier in the track; `tools/build.py` fails if not. A new
   chapter's `requires` matches its "How to read this" line.

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
python3 tools/new.py concept 03.01 slug "Title"     # also: exercise, case, story, lld, deepdive
python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py   # prove the tests work
node tools/check_page.js <page.html> [--shots DIR]  # console errors, offline, 390px scroll, markup
```

## Layout

- `curriculum.json`: source of truth. `track` is the learning order (weekly
  stages with steps and a milestone mock each, then an onsite stage and company
  packs that start when an onsite is booked; topics left off it are deferred).
  `sections` hold the topics (ids like `02.02`, tags P0/P1/P2, `requires`,
  timed `drills`).
- `sections/NN-slug/concepts/*.html`: chapters, each with
  `<meta name="topic" content="NN.MM">`.
- `sections/NN-slug/exercises/name.py` + `test_name.py`: stub and tests. The
  stub's docstring has a `Topic: NN.MM` line.
- `sections/15-interview-formats/mock-log.md`: one row per mock interview.
- `assets/`: `style.css` (theme tokens, book styles), `shell.js` (top bar,
  chapter sidebar, contents rail, Appearance panel, jump-to palette, code colors), `book.js` (quick checks, review),
  `viz.js` (`V.el`, `V.s`, `V.cells`, `V.player`, `V.binaryTree`, `V.graph`),
  `app.js`, `curriculum.js` (generated).
- `templates/`: page and exercise skeletons, worksheets, and the style guide.
