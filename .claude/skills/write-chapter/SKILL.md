---
name: write-chapter
description: Write or rewrite a swe-lab chapter in the book format, with quick checks and exercises whose tests measure work. Use when asked to write, rewrite or extend a chapter.
---

# Write a chapter

Goal: after one read, top to bottom, Danish can explain the topic in a senior
interview without the page open. How to explain comes from the `teach` skill;
this skill covers the page and the exercises.

## Plan before any HTML

1. Read `templates/README.md` (the format spec) and the reference chapter
   `sections/02-algorithms/concepts/sorting.html`.
2. Find the topic in `curriculum.json`: its id, tag, `requires` (what the
   reader already knows) and its place in the `track`. Teach nothing that
   leans on a topic later in the track; if the chapter truly needs one, move
   it or the topic in the track rather than assume it.
3. Write a short plan using `teach` steps 1–5:
   - The **pain**: one concrete story with real numbers for section 1.
   - The **rebuild**: 6–11 sections, each one idea or one fix that the
     previous section's flaw forces.
   - The **picture** for each section: the physical analogy, worked
     numbers or visualization that carries it. If a section has none, it
     isn't broken down far enough yet.
   - The **hard ideas**, where people get confused or interviewers probe.
     They get 2–3× the space: another example, a picture, an "another way"
     aside, a quick check.
   - **Go deeper** material: real systems, failure modes, proofs, and for
     design topics the constraint table.

## Build the page

- Scaffold with `python3 tools/new.py concept NN.MM slug "Title"`, which copies
  the book skeleton in `templates/concept.html`.
- Each section, intuition before formalism: a sentence or two that raise
  the question → the picture (analogy, worked numbers or `.figure`) → the
  general rule and its name → code if needed → `.keyidea` → `.check`. No
  definition, formula or code before the picture.
- **Quick checks:** 3 options, one `data-correct`, wrong options are mistakes
  real people make. `.fb.wrong` re-teaches from a different angle (a new
  example, a picture in words, plugged-in numbers) and must make sense to
  someone who picked *either* wrong option. 8–10 per chapter, ids
  `check-<slug>`.
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
- Hand off to `visuals-and-layout`, then `review-chapter`.
