---
name: write-chapter
description: Write or rewrite a swe-lab chapter in the book format, with quick checks and exercises whose tests measure work. Use when asked to write, rewrite or extend a chapter.
---

# Write a chapter

Goal: after one read, top to bottom, Danish can explain the topic in a senior
interview without the page open. How to explain comes from the `teach` skill;
this skill covers the page and the exercises.

## Plan before any HTML

1. Read `templates/README.md` (the format spec and the **writing rules**) and
   `sections/01-data-structures/concepts/hash-maps.html`, the reference for
   prose.
2. Find the topic in `curriculum.json`: its id, tag, `requires` (what the
   reader already knows) and its place in the `track`. Teach nothing that
   leans on a topic later in the track; if the chapter truly needs one, move
   it or the topic in the track rather than assume it.
3. Write a short plan using `teach` steps 1–5:
   - The **pain**: one concrete problem with real numbers for section 1.
   - The **rebuild**: 6–11 sections, each one idea or one fix that the
     previous section's flaw forces. Each heading carries the standard term.
   - For each section, its **point** in one plain sentence and the **concrete
     case** that shows it: worked numbers, an example from real software or a
     visualization. If the point won't fit in one sentence, the section isn't
     broken down far enough yet.
   - The **hard ideas**, where people get confused or interviewers probe.
     They get more words in the running text and a second worked case, not
     more boxes.
   - **Go deeper** material: caveats, real systems, failure modes, proofs,
     and for design topics the constraint table.
   - The **budget**: about 6,000 words on the main path (everything but the
     collapsed asides and the exercises) and at most about 20 boxes. Decide
     what to leave out now.

## Build the page

- Scaffold with `python3 tools/new.py concept NN.MM slug "Title"`, which copies
  the book skeleton in `templates/concept.html`.
- **Write the running text first,** as one explanation that reads complete
  with no boxes. Each section opens with its point, then the concrete case,
  then the general rule and its standard name, then code if needed. No
  formula or code before the concrete case. Working (arithmetic, formulas,
  traces) goes in a `pre.plain`, a table or a code block, and the sentence
  after it says what it shows.
- **Then add boxes only where they earn the interruption:**
  - **Quick checks** at the end of a section, where a reader could predict
    wrong: usually 5–8 per chapter, none for a section with nothing to
    predict. 3 options, one `data-correct`, wrong options are mistakes real
    people make. `.fb.wrong` re-teaches from a different angle (a new worked
    case, plugged-in numbers) and must make sense to someone who picked
    *either* wrong option. Ids `check-<slug>`.
  - **Key ideas:** two or three per chapter, for the ideas the rest hangs on.
  - **Asides:** "Go deeper" for caveats and real systems, "Explain it another
    way" for a second route into a hard idea.
- **Code** blocks are 5–15 lines of Python with comments on the lines that
  matter.
- Close with "What to say in the interview" (a 3–5 step script), `#summary`,
  `#review`, `#exercises`, `chapter-nav`.

## Exercises

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

## Finish

- In a scratch folder **outside the repo**, write a reference solution and a
  correct-but-slow one, then run
  `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`.
  It confirms the stub fails, the reference passes and the slow one fails.
  Delete the scratch folder after.
- Set the topic's `requires` in `curriculum.json` to the chapters the "How to
  read this" line names, then `python3 tools/build.py`. It warns when the two
  disagree and fails if a requirement comes later in the track.
- Run `python3 tools/check_prose.py <page>` and fix what it prints: reword
  the sentence, move the working into a block, or cut.
- Hand off to `visuals-and-layout`, then `review-chapter`.
