"""
Heavy hitters with k counters (Misra-Gries)
Topic: 02.13  |  Priority: P2

Problem
-------
Section 9 of the chapter. Billions of requests stream past. Which IPs make
up more than 1% of them? An exact count needs a counter for every distinct
IP, which can be hundreds of millions. Misra-Gries keeps only k counters
and still never misses a heavy item.

    mg = MisraGries(2)
    for x in "aabacad":
        mg.add(x)
    mg.counters()    -> {'a': 3, 'd': 1}   # a really appeared 4 times
    mg.estimate("a") -> 3, mg.estimate("b") -> 0, mg.n -> 7
    # The 5th item, c, met two full counters: a and b each lost one, and c
    # was not stored. Three occurrences (one a, one b, one c) cancelled out.

1. class MisraGries(k)
   - add(item): count one more occurrence. If the item has a counter, add
     1. Otherwise, if fewer than k counters exist, start one at 1.
     Otherwise subtract 1 from every counter and drop the ones that reach
     0 (the new item is not stored).
   - estimate(item) -> int: its counter, or 0 if it has none.
   - counters() -> dict: a copy of {item: counter}, at most k entries.
   - n: an attribute (or property), how many items were added in total.
   - The guarantee the tests check, for every item x after any prefix of
     the stream:  estimate(x) <= true count of x <= estimate(x) + n / (k + 1).
     So every item with a true count above n / (k + 1) still has a counter.
   - Target: O(1) amortized per add (the "subtract from everyone" step is
     O(k), but it can't happen often: why?), O(k) memory.

2. heavy_hitters(make_stream, k) -> dict
   - make_stream() returns a fresh iterator over the same stream each time
     you call it. You may call it at most twice (two passes).
   - Return {item: exact count} for exactly the items whose true count is
     greater than n / (k + 1), where n is the length of the stream.
   - Target: O(n) time, O(k) memory: pass 1 finds at most k candidates,
     pass 2 counts only those.

What the tests measure
----------------------
- The guarantee above, checked against an exact count after every add on
  small random streams, and at the end on a large skewed one. Space-Saving
  (evict the smallest counter and let the newcomer inherit its count) is a
  good algorithm too, but it overestimates, so it fails this test.
- Never more than k counters, at any moment.
- Memory: 300,000 items over 100,000 distinct values with k = 20, under
  tracemalloc. The peak must stay under 64 KB; a full Counter takes
  megabytes.
- Speed: k = 20,000 under a 10 s cap: 10,000 items that stay heavy, then
  220,000 new ones. Done right it's well under a second; a step that looks
  at all k counters on every add (even a fast built-in like min(values),
  `0 in values`, or a scan for a counter at zero) is billions of steps.

Before you code (say it out loud)
---------------------------------
1. Each "subtract from everyone" step throws away k + 1 occurrences (whose?).
   How many such steps can a stream of n items have?
2. Why does that bound how far below the truth any counter can be?
3. With k = 1 this is the Boyer-Moore majority vote. What does it promise?
4. Why does the second pass matter? What can go wrong if you report the
   counters as they are?

Run:  pytest -k misra_gries
"""


class MisraGries:
    def __init__(self, k):
        raise NotImplementedError

    def add(self, item):
        raise NotImplementedError

    def estimate(self, item):
        raise NotImplementedError

    def counters(self):
        raise NotImplementedError


def heavy_hitters(make_stream, k):
    raise NotImplementedError
