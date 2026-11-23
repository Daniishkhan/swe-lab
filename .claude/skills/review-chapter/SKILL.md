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

1. **As a first-time visual/analogy learner (smart high schooler).**
   - **"Why should I care?" & front-loaded jargon:** Does Section 1 make you
     care *why* this exists and show the payoff before opening the hood? Flag
     any unintroduced jargon or Big-O wall in the title, intro, or
     `.learn-list`.
   - **Running physical analogy:** Is there **one consistent physical analogy**
     carried through the rebuild (with its limits named), placed *before*
     formulas, jargon, and code? Worked numbers alone do **not** count as a
     picture.
   - **Verbiage & voice:** Flag every sentence you read twice, every term used
     before it is defined, every dry conclusion-first textbook opener ("X is a
     Y that…"), every unexplained symbol, and any heavy manual arithmetic that
     stalls intuition before the idea lands.
   - **Visual pacing:** Confirm there is a visual in Section 1 or 2, and flag
     any span of 3+ consecutive sections without a visual (`.figure`, inline
     SVG, or `.diagram` — plain tables and code blocks do not count).
   - **Scope & cognitive load:** Is the visible main path lean (~2,000–3,500
     words, ~12–20 min) and focused on **one core mental model**? Flag any
     secondary architecture, heavy combinatorics/proof, language runtime
     internal, or security/history deep dive sitting in the main path instead
     of `details.aside.deeper` or a separate Part 2.
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
3. **As a senior interviewer (with the layering guardrail).**
   - What follow-up would you ask that the chapter doesn't prepare Danish for?
     Trade-offs, real systems, failure modes, "what if it doesn't fit in
     memory, arrives as a stream, runs on 100 machines".
   - Could a reader who memorized the summary answer "why this and not the
     obvious alternative?" If not, the chapter teaches names, not reasons.
   - **Layering rule (critical):** For every missing senior topic you flag,
     specify *where* it belongs — core mental model / "How it breaks" / "What
     to say" in the main path, vs. secondary architectures, proofs, or runtime
     internals in **`details.aside.deeper`** (or a **Part 2** chapter). **Never
     fix an interviewer gap by bloating the first-pass main explanation.**

## Check the learning machinery and data flow

- **Data flow:** Confirm the chapter moves cleanly through
  `Why care (pain + payoff) → Running analogy & rebuild → How it breaks → Interview patterns → Spoken script`.
  Practical interview patterns must have concrete before/after examples —
  never buried as a tiny afterthought table at the end.
- **Quick checks (5–8):** Every check must test **mental models, predictions,
  or "what breaks if X changes"** — flag and replace any check that tests
  detached math/probability trivia or pure terminology recall. Exactly one
  defensible answer; wrong options are plausible mistakes; `.fb.wrong` teaches
  from a different angle instead of repeating `.fb.right`.
- The hardest ideas got the most space; easy ones aren't padded.
- Exercises cover the key ideas. Prove the tests measure work: write a
  correct-but-slow solution in a scratch folder outside the repo and run
  `python3 tools/check_exercise.py <name> --pass ref.py --fail slow.py`.
  Tests aren't flaky (seeded randomness, generous budgets, no tight timing).
  Stubs contain no solutions.
- `node tools/check_page.js <page>` is clean.

## Report and fix

List findings, most serious first, grouped as **Wrong** (facts, code),
**Unclear / Too Complex** (missing analogy, jargon, textbook voice, visual
desert, bloated main path, weak data flow), **Missing**, **Nits**. Each has:
where (section id or line), what's wrong, why it matters, and the fix
(including whether an addition belongs in the main path, `details.aside.deeper`,
or a Part 2). Fix them and review again until **Wrong** and **Unclear / Too
Complex** are empty.
