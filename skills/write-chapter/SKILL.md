---
name: write-chapter
description: Write or rewrite a swe-prep chapter in the book format, with quick checks and exercises whose tests measure work. Use when asked to write, rewrite or extend a chapter.
---

# Write a chapter

Goal: a chapter Danish can read top to bottom and come out able to explain the
topic in an interview, at senior level, in his own words.

## Before writing

1. Read `CLAUDE.md`, `templates/README.md` ("Book chapters"), and one reference
   chapter (`sections/02-algorithms/concepts/sorting.html`). Copy its head,
   structure and class names exactly.
2. Find the topic in `curriculum.json`. Note its id, tag and the neighboring
   chapters (for the `chapter-nav` links and for what the reader already knows).
3. Write a plan before any HTML, as a short list:
   - The **one problem** the chapter opens with (a concrete story, not a
     definition).
   - 6–11 sections, each one idea, each building on the last.
   - Which ideas are **hard** (where people get confused or interviews probe).
     These get 2–3× the space: more examples, a picture, an "another way"
     aside, a quick check.
   - The senior-level material for "Go deeper" asides (real systems, trade-offs,
     failure modes, proofs).

## Writing rules

- **Voice:** a smart high schooler should follow every sentence. Short
  sentences. One idea per paragraph. Define each term in plain words the first
  time it appears, then use it consistently.
- **Concrete first, abstract second:** example with real numbers → the general
  rule → the name for it.
- **Analogies** come from everyday life (cards, queues, post offices, bouncers)
  and you say where the analogy breaks if it matters.
- **Code** is short Python, 5–15 lines, with comments on the lines that matter.
  Show code after the idea is clear in words, not instead of it.
- Each section ends with a `.keyidea` (one or two sentences) and, for anything
  non-trivial, a `.check`.
- **Quick checks:** 3 options, one `data-correct`. Wrong options are the
  mistakes real people make. The `.fb.wrong` text re-teaches the idea from a
  different angle (a new example, a picture in words, plugging in numbers). It
  must make sense to someone who picked *any* wrong option. Aim for 8–10
  checks per chapter, with ids `check-<slug>`.
- Never write "simply", "obviously", "trivially", "it's easy to see".
- Close with: "What to say in the interview" (a 3–5 step script),
  `#summary` (numbered, one line each), `#review`, `#exercises`, `chapter-nav`.

## Exercises

- 2–3 **warm-ups** on paper (tracing, picking the right tool, breaking a naive
  approach). Answers may go in a collapsed `details.aside`.
- 3–6 **core** coding exercises in `sections/NN-slug/exercises/<unique_name>.py`
  with `test_<unique_name>.py`. Stubs raise `NotImplementedError`; the module
  docstring lists each function, its target complexity and a "say it out loud"
  prompt, plus `Topic: NN.MM`.
- Tests check correctness **and measure work**: wrap inputs in objects that
  count comparisons or reads, count copies or multiplications, or use a size
  where the slow approach is clearly over a generous limit. Avoid wall-clock
  timing unless the gap is 100× or more. Seed any randomness.
- 1–2 **stretch** items: a design question, a measurement experiment, or a
  timed "explain it out loud".

## Finish

- Verify tests with reference solutions in a scratch folder **outside the
  repo**; confirm the stubs fail. Never commit the solutions.
- `python3 tools/build.py`.
- Then hand off to `plan-visuals`, `design-layout` and `review-chapter`.
