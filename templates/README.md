# Templates and house style

`python tools/new.py ...` copies these files into the right chapter and fills in
the placeholders. This page is the style guide that keeps new pages consistent
with chapters 1 and 2.

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
  real numbers. Define every term the first time it appears.

## Concept pages, box format (`concept.html`, older pages)

Each page is a stack of collapsible **group boxes** (`<details class="box">`).
Keep this order and delete panes that don't apply:

| Pane | Class | What goes in it |
|---|---|---|
| The one-sentence idea | `box accent` | One or two sentences you could say in an interview. |
| Why / the problem it solves | `box` | Start from the pain. Concrete scenario. |
| From first principles | `box` | Build it up in numbered steps; each step fixes the previous one's flaw. |
| Analogy / physical picture | `box analogy` | A real-world analogy **and where it breaks down**. |
| Playground | `box viz` | An interactive visualization (see below). |
| Costs | `box` | Complexity / trade-off table. |
| What a senior answer adds | `box senior` | Trade-offs, failure modes, real systems, operational concerns. |
| Traps | `box trap` | Mistakes people confidently make. |
| Check yourself | `box` | `<details class="qa">` question/answer toggles. |
| Practice | `box` | Link the exercise in `../exercises/` plus classic problems. |

Voice: second person, plain sentences, no filler. Lead with the intuition, then
the mechanics. Name real systems (Redis, Postgres, the Linux kernel) when they
use the idea. Every claim about complexity says whether it's average, worst, or
amortized.

## Visualizations

Use the helpers in `assets/viz.js` (no libraries, no build step):

- `V.player(el, { frames, draw })`: step-through player (prev / play / next / speed).
  Build an array of frames up front; each frame can carry a `msg` caption.
- `V.cells(values, { cls, ptrs })`: an array drawn as cells with indexes and pointer labels.
- `V.binaryTree(svg, root, { cls })`: lays out and draws `{val, left, right}` trees.
- `V.graph(svg, nodes, edges, { directed })`: node-link graph with fixed coordinates.

Colors come from CSS variables in `assets/style.css`, so visuals work in both
themes automatically. Cell/node classes: `hl` (current), `warn` (compared or
frontier), `done` (final), `bad` (rejected), `win` (in window), `dim`.

## Exercises (`exercise.py`, `test_exercise.py`)

- The docstring states the problem, requirements, target complexity, and the
  "say it out loud" questions. Keep the `Topic: XX.YY` line: the build script
  uses it to link the exercise to its topic.
- Stubs raise `NotImplementedError`. Never commit a solution in a stub you
  generate for someone else.
- Tests cover the prompt's example, empty/smallest input, duplicates,
  boundaries, and (where cheap) a randomized check against a brute force.
- Module names must be unique across the repo.

## Markdown worksheets

`design-case.md` (45-minute system design), `star-story.md` (behavioral),
`lld-worksheet.md` (object-oriented design), `mock-log.md` (mock interview log).
