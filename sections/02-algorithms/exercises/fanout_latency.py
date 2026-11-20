"""
Fan-out and tail latency
Topic: 02.16  |  Priority: P2

Problem
-------
Sections 8 to 10 of the chapter. One user request fans out to n backends
in parallel and waits for all of them, so it is as slow as the slowest one.
Each backend is independent and is "slow" with probability p_slow.

    prob_any_slow(0.01, 100)      -> 0.63397   # 1 - 0.99^100
    max_fanout(0.01, 0.5)         -> 68        # at most 50% of requests slow
    fanout_quantile(samples, 100, 0.99)        # the request's p99 is the
                                               # backend's p99.99

Requirements
------------
- prob_any_slow(p_slow, n) -> float: the chance that at least one of n
  backends is slow. 0 <= p_slow <= 1, n >= 0. Relative error at most 1e-6,
  also when p_slow is tiny (1e-12): 1 - p_slow rounds in floats, so work
  with "log of 1 + tiny" and "e^tiny - 1" (both are in the math module).
- max_fanout(p_slow, max_prob) -> int: the largest n >= 0 with
  prob_any_slow(p_slow, n) <= max_prob. Raise ValueError unless
  0 < p_slow < 1 and 0 <= max_prob < 1. O(1): the answer can be 10^11, so
  no loop that tries n = 1, 2, 3, ... The tests' exact-boundary cases use
  p_slow = 0.5, where every power is exact in binary, so "<= max_prob" has
  one clear answer there. Elsewhere a formula's candidate can land one off
  from float rounding, so check it and its neighbour with prob_any_slow.
- fanout_quantile(samples, n, q) -> one of the samples. samples is one
  backend's measured latencies (any order; each sample equally likely); every
  backend draws independently from it. Return the q-quantile of the
  request's latency, the max over n backends, using the nearest-rank rule:
  the smallest sample v such that P(request latency <= v) >= q.
  Raise ValueError if samples is empty, n < 1, or q is not in (0, 1].
  Don't modify samples. Read each sample O(1) times: sort once, then pick
  ONE rank by arithmetic. No simulation: it is slow and not exact.

What the tests measure
----------------------
- prob_any_slow against values worked out offline with 60-digit decimals.
- max_fanout at known answers, including 693,147,180 and 105,360,515,657,
  under a 2 s cap per test.
- fanout_quantile on samples built so the answer is known (the latencies
  1, 2, ..., N ms shuffled, and a 99%-fast/1%-slow mix). Only where q^(1/n) * N is
  exactly a whole number may the rank be off by one, since floating point
  can land a hair either side of it; everywhere else the rank is exact.
  The samples come in a sequence that counts every item it hands out (budget
  3N + 100 reads) and refuses writes; scanning all samples once per
  candidate costs N^2 reads and fails.

Before you code (say it out loud)
---------------------------------
1. Why is the chance that ALL n backends are fast (1 - p)^n? What
   assumption makes multiplying allowed, and when is it false?
2. P(max of n <= v) = P(one <= v)^n. Why does that turn the request's q
   quantile into the backend's q^(1/n) quantile?
3. With 100 backends and a 1%-slow tail, what is the median request
   latency? What would you change in the system?

Run:  python3 -m pytest -k fanout_latency
"""


def prob_any_slow(p_slow, n):
    raise NotImplementedError


def max_fanout(p_slow, max_prob):
    raise NotImplementedError


def fanout_quantile(samples, n, q):
    raise NotImplementedError
