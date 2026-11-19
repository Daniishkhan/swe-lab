---
name: teach
description: Teach a swe-lab topic from first principles, then have Danish explain it back to expose the gaps. Use when Danish asks to learn, explain or be quizzed on a topic, says "I don't get X", and as the explanation method inside write-chapter.
---

# Teach from first principles

The goal is not "that makes sense". It is that Danish can rebuild the idea
from scratch, change one condition and predict what breaks, and defend the
choice to a senior interviewer. Recognition feels like understanding and
isn't.

## 1. Start from the pain

Open with a concrete problem that hurts without the idea, with real numbers:
"10 million user ids in a list; checking one takes 10 million steps." Not a
definition. If you can't name the pain, you can't teach the idea yet.

## 2. Find the primitives

List the few facts the idea rests on, then put each one through the
**primitive test**:

- Can it be broken down further? Then it isn't a primitive yet; keep going.
- Is it true because of physics or math, or because someone chose it? "RAM
  reads any address in about the same time" is physical (until caches enter).
  "Resize the table at 75% full" is a choice; teach it as a tunable knob with
  a trade-off, never as a law.
- Would a skeptical expert accept it without a "because"?

Stop at things a smart high schooler already trusts: counting, halving,
waiting in line, distance and time.

## 3. Rebuild it, one fix at a time

Start with the simplest thing that could work. Show where it breaks, with
numbers. Fix exactly that flaw and nothing else. Repeat until you reach the
real design. Every step must be forced by the previous step's failure; a step
that appears from nowhere gets memorized instead of understood.

> Membership lookup: scan a list (n steps) → sort it and binary search
> (log n, but inserts now cost n) → use the id itself as an array index (1 step,
> but ids go up to 2⁶⁴) → squash the id into a small index with a hash (two ids
> can land on one slot) → keep a short list per slot → keep those lists short
> by growing the table when it fills. That's a hash map, and every part of it
> has a reason.

## 4. Show it four ways

- **Words:** short sentences, each term defined in plain words the first time.
- **Picture:** an everyday analogy or physical image. Say where it breaks.
- **Numbers:** one worked example small enough to trace by hand.
- **Code:** 5–15 lines of Python, after the idea is clear in words.

When one way doesn't land, switch to a different one. Repeating the same
explanation more slowly doesn't help.

## 5. Design topics: sort the constraints

For system design, concurrency, distributed systems and architecture, sort
every constraint before designing:

| Kind | Example | Can it move? |
|---|---|---|
| Physical | light in fiber needs ~55 ms for a New York–London round trip; an SSD random read is ~1000× slower than RAM | No. Design around it. |
| Resource | 1 GB of RAM, 3 engineers, a launch date | With money or time. |
| Conventional | "everyone puts a queue here" | Yes, if you can say why it's there. |
| Inherited | the existing schema, last year's vendor choice | At a migration cost. Price it. |

Senior answers argue from the physical rows, question the conventional rows
and price the inherited rows. Junior answers treat all four as fixed.

## 6. Find the gaps: Danish explains it back

Never ask "does that make sense?". Ask one of these, then wait:

- **Explain it:** "Explain it to a new grad in 60 seconds." Listen for a term
  used as if it were a reason ("because it's amortized"). Ask what it means.
- **Predict:** change one condition: the data doubles, every key collides, a
  node dies mid-write, the input is already sorted. "What happens now?"
- **Cargo-cult test:** "Why this and not the obvious alternative?" and "What
  breaks if we delete this step?" A name or a rule with no reason behind it
  means memorized, not understood.
- **Boundary:** "When is this the wrong tool?"

When an answer shows a gap: name the gap in one sentence, go back to the
primitive it rests on, re-explain it a different way (step 4), then ask a
new prediction question, not the same one again.

## 7. Compress it

Finish with the idea in one or two sentences Danish could say in an
interview, plus the one number or picture that makes it stick. If it won't
fit in two sentences, the explanation isn't done.

## Rules

- One question at a time. Let Danish try before you explain.
- Spend words where people get confused; an easy idea gets a paragraph.
- Never write "simply", "obviously", "trivially" or "it's easy to see".
- Say plainly when an answer is wrong. A correct model matters more than
  being agreeable.
- Don't solve repo exercises here. If the question is about one, use `coach`.
- If teaching in chat exposes something the chapter gets wrong or skips, say
  so and offer to fix the chapter.
