---
name: write-chapter
description: Write or rewrite a swe-lab chapter in the book format, with quick checks and exercises whose tests measure work. Use when asked to write, rewrite or extend a chapter.
---

# Write a chapter

Goal: after one read, top to bottom, Danish feels *why* the idea exists, holds
a clear visual/physical mental model of how it works, knows how to use it in
coding rounds, and can explain it in a senior interview without the page open.
How to explain comes from the `teach` skill; this skill covers planning, data
flow, scope, voice, the page, and the exercises.

## 1. Plan the blueprint before any HTML

Do not open an HTML file until you have written a short blueprint covering all
five items below:

1. **Context:** Read `templates/README.md` (the format spec) and the reference
   chapter `sections/02-algorithms/concepts/sorting.html`. Look up the topic in
   `curriculum.json`: its id, tag, `requires` (what the reader already knows),
   and its place in the `track`. Teach nothing that leans on a topic later in
   the track; if the chapter truly needs one, move it or the topic in the track
   rather than assume it.
2. **"Why should I care?" hook (Pain + Payoff):**
   - One concrete pain story with real numbers for Section 1.
   - The immediate payoff: a 2–4 bullet preview of the superpower this unlocks
     in real software and interviews (e.g., turning a nested loop into one
     pass), shown *before* opening the hood.
3. **One running anchor analogy:**
   - Choose a **single everyday physical model** (e.g., coat-check room with
     numbered hooks, hand of playing cards, filing cabinet) that carries across
     the entire rebuild, and note explicitly where it breaks.
   - Worked numbers alone do **not** satisfy "picture first" — every core
     concept must map back to the analogy or a visual.
4. **Data-flow outline (canonical chapter arc):**
   - **Header, intro, `.learn-list`:** Plain English only. **Zero unintroduced
     jargon or Big-O walls** before Section 1.
   - **Section 1 — Why do we even need this?** Pain story + early visual
     before/after + immediate payoff preview.
   - **Sections 2–6 — The rebuild (4–6 sections):** One fix per section, each
     forced by the previous step's failure. Frame headings as **questions or
     tension** (`Question → Naive attempt → Break → Fix`), never textbook
     labels.
   - **How can this break? (1 section):** The 2–4 core gotchas interviewers
     probe, worst-case behavior, and when this is the *wrong* structure —
     grounded in the running analogy.
   - **How you use this in interviews (1 section):** The 3–5 practical coding
     patterns with a concrete before/after (visual or short code showing what
     work disappears) — never buried as a tiny afterthought table.
   - **What to say in the interview (1 section):** A 3–5 step spoken script.
   - **Close:** `#summary`, `#review`, `#exercises`, `chapter-nav`.
5. **Scope, layering, and visual map:**
   - **Budget per chapter:** Aim for **~2,000–3,500 visible words (~12–20 min
     read)**, **6–9 numbered sections**, and **5–8 quick checks**.
   - **One core mental model per chapter (the Layering Rule):** Keep the main
     reading path lean and intuitive. Move **secondary architectures** (e.g.,
     open addressing + tombstones alongside separate chaining), **heavy math or
     proofs** (e.g., birthday paradox combinatorics), **language runtime
     internals** (e.g., CPython `perturb`, Java tree bins, Swiss tables), and
     **historical/security deep dives** into collapsed `details.aside.deeper`
     boxes — or **split the topic into Part 1 (Intuition, Core & Patterns) and
     Part 2 (Under the Hood)** when the deeper layer deserves its own
     interactive playground.
   - **Hard ideas** get 2–3× the space: a visual, a second angle
     (`details.aside.another`), and a quick check.
   - **Visual map:** List every planned visual before drafting prose. Plan an
     **early visual in Section 1 or 2**, and allow **at most 2 consecutive
     sections without a visual** (mixing lightweight inline SVGs / `.diagram`
     blocks with interactive `V.player` / playgrounds).

## 2. Build the page

- Scaffold with `python3 tools/new.py concept NN.MM slug "Title"`, which copies
  the book skeleton in `templates/concept.html`.
- **Voice:** Write like a sharp mentor talking to a smart friend — warm,
  direct, curious, conversational. Never open a section with a dry textbook
  definition or conclusion-first thesis statement ("A hash function is…"). Open
  with the question or tension left by the last step.
- **Order inside every section (strictly intuition before formalism):**
  1. 1–2 sentences raising the question or tension.
  2. The picture (running analogy and/or `.figure` / SVG / `.diagram`).
  3. Small mental-math numbers (3–8 items you can trace in your head; keep
     production arithmetic like base-31 hashing or huge exponents in
     `details.aside.deeper`).
  4. The plain-English rule *first*, then its CS name or symbol (e.g.,
     "crowdedness" before "load factor `α`").
  5. 5–15 lines of commented Python, only if it adds clarity.
  6. `.keyidea` → `.check`.
- **Quick checks (5–8 per chapter, ids `check-<slug>`):**
  - Test **mental models, predictions, and "what breaks if X changes"** — never
    detached math/probability trivia (e.g., birthday paradox calculations) or
    pure terminology recall.
  - 3 options, one `data-correct`, wrong options are mistakes real people make.
  - `.fb.wrong` re-teaches from a *different* angle (new example, physical
    picture, plugged-in numbers) and must make sense to someone who picked
    *either* wrong option.
- **Code** blocks are 5–15 lines of Python with comments on the lines that
  matter.

## 3. Exercises

- **Warm-ups (2–3), on paper:** tracing, picking the tool, breaking a naive
  approach. Answers may sit in a collapsed `details.aside`.
- **Core (3–6), code:** `python3 tools/new.py exercise NN.MM <unique_name>`.
  Stubs raise `NotImplementedError`. The docstring lists each function, its
  target complexity, a "say it out loud" prompt, and `Topic: NN.MM`.
- Tests check correctness **and measure work**: count comparisons, reads or
  copies through wrapper objects (see `test_sorts.py`), or use a size where
  the slow approach is far over a generous budget. Wall-clock timing only for
  gaps of 100× or more. Seed all randomness.
- **Stretch (1–2):** a design question, a measurement experiment, or a timed
  "explain it out loud".

## 4. Finish

- In a scratch folder **outside the repo**, write a reference solution and a
  correct-but-slow one, then run
  `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`.
  It confirms the stub fails, the reference passes and the slow one fails.
  Delete the scratch folder after.
- Set the topic's `requires` in `curriculum.json` to the chapters the "How to
  read this" line names, then `python3 tools/build.py`. It warns when the two
  disagree and fails if a requirement comes later in the track.
- Hand off to `visuals-and-layout`, then `review-chapter`.
