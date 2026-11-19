---
name: review-chapter
description: Adversarially review a swe-prep chapter for wrong facts, confusing explanations, gaps an interviewer would probe, and weak quick checks or tests. Use after writing or changing a chapter.
---

# Review a chapter adversarially

You are not the author. Your job is to find what's wrong, unclear or missing
before Danish trusts it in an interview. Assume there are problems; a review
that finds nothing is suspicious. Prefer running this as a fresh subagent that
gets the file paths, not the author's reasoning.

## Read it three ways

1. **As a high schooler.** Mark every sentence you had to read twice, every
   term used before it's defined, every jump between sections that skips a
   step, and every code block that appears before the idea is clear.
2. **As a skeptical expert.** Check every claim, number and complexity:
   - Recompute the numbers (step counts, n log n values, table rows, "how long
     would it take" estimates). Run a quick script when you can.
   - Is the Big-O right for best, average, worst, and space? Amortized vs
     worst-case confused? Hidden costs (slicing, string concat, `in` on a list)?
   - Is the code correct, including edge cases (empty, one item, duplicates,
     negatives)? Does it match the prose?
   - Are analogies misleading anywhere they're used?
3. **As a senior interviewer.** What follow-up would you ask that the chapter
   doesn't prepare him for? Missing trade-offs, real-world systems, failure
   modes, "what if the data doesn't fit in memory / is a stream / is
   distributed"? Those belong in "Go deeper" or the interview script.

## Check the learning machinery

- Each quick check: exactly one defensible right answer; wrong options are
  plausible mistakes; the wrong-answer feedback teaches differently instead of
  repeating the right-answer text.
- The hardest ideas got the most space. Easy ones aren't padded.
- The exercises cover the chapter's key ideas, and the tests really fail a
  slow-but-correct solution (write one in scratch and run it). Tests aren't
  flaky (seeded randomness, generous limits, no tight timing). The stubs
  contain no solutions.

## Report

List findings, most serious first, each with: where (section id or line),
what's wrong, why it matters, and the concrete fix. Group them as
**Wrong** (factual or code errors), **Unclear**, **Missing**, **Nits**.
Then fix them (or hand them back to the author) and review again until there
is nothing in Wrong or Unclear.
