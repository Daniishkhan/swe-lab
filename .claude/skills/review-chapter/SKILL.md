---
name: review-chapter
description: Adversarially review a swe-lab chapter for wrong facts, confusing explanations, gaps an interviewer would probe, and weak quick checks or tests. Use after writing or changing a chapter.
---

# Review a chapter adversarially

You are not the author. Find what is wrong, unclear or missing before Danish
relies on it in an interview. Assume there are problems; a review that finds
nothing is suspicious. Run it as a fresh subagent given only the file paths,
not the author's reasoning.

## Read it three ways

1. **As a smart high schooler.** Mark every sentence you read twice, every
   term used before it's defined, every jump that skips a step, every
   section that gives a definition, formula or code before a picture or
   worked example, and every idea that is named rather than built up from
   simpler facts.
2. **As a skeptical expert.**
   - Recompute every number: step counts, n log n values, table rows, "how
     long would it take" estimates. Run a script.
   - Big-O for best, average, worst and space. Amortized vs worst case kept
     apart. Hidden costs named (slicing, string concatenation, `in` on a list).
   - Code correct on empty, one item, duplicates, negatives, and matching the
     prose.
   - Primitive test: is anything presented as a law that is really a
     convention or a tunable choice?
   - Analogies: where do they mislead?
3. **As a senior interviewer.** What follow-up would you ask that the chapter
   doesn't prepare Danish for? Trade-offs, real systems, failure modes, "what
   if it doesn't fit in memory, arrives as a stream, runs on 100 machines".
   Could a reader who memorized the summary answer "why this and not the
   obvious alternative?" If not, the chapter teaches names, not reasons.

## Check the learning machinery

- Quick checks: exactly one defensible answer; wrong options are plausible
  mistakes; the wrong feedback teaches it a different way instead of
  repeating the right-answer text.
- The hardest ideas got the most space; easy ones aren't padded.
- Exercises cover the key ideas. Prove the tests measure work: write a
  correct-but-slow solution in a scratch folder outside the repo and run
  `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`.
  Tests aren't flaky (seeded randomness, generous budgets, no tight timing).
  Stubs contain no solutions.
- `node tools/check_page.js <page>` is clean.

## Report and fix

List findings, most serious first, grouped as **Wrong** (facts, code),
**Unclear**, **Missing**, **Nits**. Each has: where (section id or line),
what's wrong, why it matters, the fix. Then fix them and review again until
Wrong and Unclear are empty.
