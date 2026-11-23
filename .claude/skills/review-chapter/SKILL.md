---
name: review-chapter
description: Adversarially review a swe-lab chapter for wrong facts, confusing explanations, text to cut, gaps an interviewer would probe, and weak quick checks or tests. Use after writing or changing a chapter.
---

# Review a chapter adversarially

You are not the author. Find what is wrong, unclear, too long or missing
before Danish relies on it in an interview. Assume there are problems. Run it
as a fresh subagent given only the file paths, not the author's reasoning.

A review may not make the chapter longer or harder to read. Most fixes are a
corrected sentence or a cut.

## Read it four ways

1. **As an engineer new to the topic, reading aloud.** Mark every sentence
   you read twice or couldn't say aloud (arithmetic, arrows, semicolons or
   stacked brackets inside it), every term used before it's defined, every
   jump that skips a step, every section whose first sentence doesn't state
   its point, every heading or link that isn't the standard term, and every
   idea that is named rather than built up from simpler facts.
2. **As a skeptical expert.**
   - Recompute every number: step counts, n log n values, table rows, "how
     long would it take" estimates. Run a script.
   - Big-O for best, average, worst and space. Amortized vs worst case kept
     apart. Hidden costs named (slicing, string concatenation, `in` on a list).
   - Code correct on empty, one item, duplicates, negatives, and matching the
     prose.
   - Primitive test: is anything presented as a law that is really a
     convention or a tunable choice?
   - Analogies: more than one everyday analogy? Does its vocabulary replace
     the real terms? Where does it mislead?
3. **As a senior interviewer.** What follow-up would you ask that the chapter
   doesn't prepare Danish for? Trade-offs, real systems, failure modes, "what
   if it doesn't fit in memory, arrives as a stream, runs on 100 machines".
   Could a reader who memorized the summary answer "why this and not the
   obvious alternative?" If not, the chapter teaches names, not reasons.
4. **As an editor with a budget.** Run `python3 tools/check_prose.py <page>`
   and read what it prints. Then, for each paragraph, box and aside: what
   would the reader lose if it were gone? Mark what to cut, what to move to
   "Go deeper", every caveat sitting in the running text, and every place
   the running text stops making sense when the boxes are skipped.

## Check the learning machinery

- Quick checks: exactly one defensible answer; wrong options are plausible
  mistakes; the wrong feedback teaches it a different way instead of
  repeating the right-answer text. Each sits at the end of its section.
- The hardest ideas got the most words; easy ones aren't padded.
- Exercises cover the key ideas. Prove the tests measure work: write a
  correct-but-slow solution in a scratch folder outside the repo and run
  `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`.
  Tests aren't flaky (seeded randomness, generous budgets, no tight timing).
  Stubs contain no solutions.
- `node tools/check_page.js <page>` is clean.

## Report and fix

List findings, most serious first, grouped as **Wrong** (facts, code),
**Unclear**, **Cut** (too long, repeats, interrupts), **Missing**, **Nits**.
Each has: where (section id or line), what's wrong, why it matters, the fix.

Rules for fixes:

- Correct the sentence itself. Never patch it with a bracket or a trailing
  caveat; if the full truth needs one, it goes in a "Go deeper" aside.
- A **Missing** item goes in the running text only if an interviewer would
  probe it at this topic's level, and then it names what to cut to make
  room. Otherwise it goes in "Go deeper" or nowhere.

Then fix them and review again until Wrong and Unclear are empty and the
prose check meets its targets.
