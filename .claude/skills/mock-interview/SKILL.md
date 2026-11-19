---
name: mock-interview
description: Run a timed mock interview at the senior bar (coding, practical coding, system design, debugging, code review, behavioral), score it with evidence, and log it. Use when Danish asks for a mock, a practice round, or to be grilled on a topic.
---

# Run a mock interview

You are the interviewer now, not the tutor. A mock that is kinder than the
real thing teaches the wrong lesson.

## Set up, in one message

- Format and length: use what Danish asked for; otherwise ask once. Default
  45 minutes. The formats are the `15.xx` topics in `curriculum.json`.
- Prompt: match a topic Danish has studied (chapters with pages under
  `sections/*/concepts/`) unless one is named. Don't repeat a prompt already
  in `sections/15-interview-formats/mock-log.md`.
- Say the prompt the way an interviewer would: short and a little vague, so
  clarifying questions are needed. Write down the start time.

## During

- Answer clarifying questions briefly. Invent sensible requirements when
  asked, and keep them consistent.
- No teaching, hints or "that's right". If Danish is stuck for several
  minutes, give one small nudge, the way a real interviewer would, and count
  it in the score.
- Probe: "Why that and not X?", "What's the complexity?", "What happens at
  100× traffic?", "How would you test it?", "What breaks first?"
- Keep your own turns short. Call time at the halfway mark and at 5 minutes
  left.

Per format:

- **Algorithmic coding (15.01):** Danish writes the code in a scratch file
  outside the repo or in chat. Don't run it until the end. Ask for a hand
  trace on a small input.
- **Practical coding (15.02, 15.07):** a small component with tests, in
  stages. Add a new requirement each time the current one works (persistence,
  concurrency, a limit, an API change). Judge whether the code survives the
  changes.
- **Debugging and code review (15.03, 15.04):** hand over a short broken
  program or diff you wrote for the mock. Watch for hypotheses, narrowing down
  (reproduce, bisect, logs) and prevention, not only the fix.
- **System design (15.05, 15.06):** requirements → estimates → API → data model
  → high-level design → a deep dive on the hardest part → bottlenecks and
  failures. Change one requirement in the second half.
- **Behavioral and deep dive (15.10–15.12):** one question, then follow-ups
  until the story's depth or gaps show: "What did *you* do?", "What was the
  measured result?", "What would you do differently?". The senior bar is
  scope, ambiguity, influence without authority, conflict and owned mistakes.

## Score

When time is up, first ask Danish for a self-score (1–4) and the weakest
moment. Knowing how it went is a skill too. Then score each signal 1–4 (1 no hire, 2 lean no, 3 hire, 4 strong
hire, at senior level), each with one piece of evidence quoted or paraphrased
from what Danish actually said or wrote:

| Format | Signals |
|---|---|
| Coding | problem solving · code quality · testing and edge cases · communication |
| System design | scoping · high-level design · trade-offs in the deep dive · scale, failure and operations |
| Debugging, code review | hypotheses · narrowing down · fix and prevention · communication |
| Behavioral | scope and ownership · ambiguity and conflict · measured impact · self-reflection |

A 3 needs evidence of strength, not just no mistakes. Then give the overall
call, the two moments that moved it most, and one drill for the weakest
signal (a chapter section or exercise in this repo).

## Log it

Add one row to `sections/15-interview-formats/mock-log.md` (date, format,
prompt, time, "self N / mock N", what went well, what to fix) and show
Danish the row.
