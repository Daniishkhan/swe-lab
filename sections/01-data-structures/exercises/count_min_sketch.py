"""
Count-Min Sketch and heavy hitters
Topic: 01.12  |  Priority: P2

Problem
-------
Build section 6 of the chapter: count how often each item appears in a
stream, in memory that doesn't grow with the number of distinct items. An
estimate is never too low, and is too high by at most epsilon * N (N = the
total of all counts) with probability at least 1 - delta.

    cms = CountMinSketch(epsilon=0.01, delta=0.01)
    cms.width, cms.depth   -> 272, 5
    for word in "to be or not to be".split():
        cms.add(word)
    cms.estimate("to")     -> 2    (never less than 2; more only on a collision)
    cms.estimate("hamlet") -> 0    (usually; a collision in every row could make it more)
    cms.total              -> 6

    heavy_hitters(iter("abracadabra"), 1) -> [("a", 5)]

Requirements
------------
1. CountMinSketch(epsilon, delta): raise ValueError unless 0 < epsilon < 1
   and 0 < delta < 1. Use section 6's sizes, exactly:
       width = ceil(e / epsilon)          (e = math.e, about 2.718)
       depth = ceil(ln(1 / delta))
   - add(item, count=1): item is a str. Raise ValueError if count < 0.
     Touches one counter per row: O(depth).
   - estimate(item): O(depth). Never below the true count.
   - total: the sum of every count added so far.
   - merge(other): a NEW sketch whose counters are the sums of both. Its
     estimates must equal those of one sketch fed both streams. Raise
     ValueError if width or depth differ. Don't modify either input.
   - Hash with hashlib (each row needs its own, independent position), never
     the built-in hash(): sketches built in different processes, or on
     different machines, must agree so they can be merged.
2. heavy_hitters(stream, k, epsilon=1e-4, delta=0.01): one pass over an
   iterable (you can't walk it twice). Return up to k (item, estimate) pairs
   with the largest estimates, largest first (ties: smaller item first).
   Memory: one sketch plus about k candidate items. Never a dict of every
   item. Section 6 shows the shape: after counting an item, look at its
   estimate and decide whether it belongs among your k candidates.

What the tests measure
----------------------
- Estimates never undercount (so "average the rows" fails), and on a skewed
  stream of 150,000 counts over 20,000 distinct items, at most 1% of items
  are over by more than epsilon * N. A single row of the same width misses
  the bound on several percent of items.
- Memory: adding 100,000 distinct items to CountMinSketch(0.001, 0.01)
  must peak under 1 MB of new allocations (its 13,595 counters take about
  110 KB; a dict of exact counts takes about 6 MB).
- merge() equals a sketch built from both streams, item for item.
- Estimates are identical in two processes with different PYTHONHASHSEED.
- heavy_hitters(stream, 10, epsilon=0.001) finds the 10 heavy items of a
  185,000-item stream with 50,000 distinct items, from a one-shot
  generator, under a 1.5 MB peak (counting every item exactly takes over
  8 MB), including when every copy of one heavy item arrives at the end.

Before you code (say it out loud)
---------------------------------
1. Why can a counter only be too high, never too low?
2. Why take the minimum over the rows, and not the average?
3. Why is the error bound epsilon * N, the total, and not a fraction of the
   item's own count? Who does that hurt?
4. In heavy_hitters, what happens to an item whose copies all arrive late?

Run:  pytest -k count_min_sketch
"""

from collections.abc import Iterable


class CountMinSketch:
    def __init__(self, epsilon: float, delta: float):
        raise NotImplementedError

    @property
    def width(self) -> int:
        raise NotImplementedError

    @property
    def depth(self) -> int:
        raise NotImplementedError

    @property
    def total(self) -> int:
        raise NotImplementedError

    def add(self, item: str, count: int = 1) -> None:
        raise NotImplementedError

    def estimate(self, item: str) -> int:
        raise NotImplementedError

    def merge(self, other: "CountMinSketch") -> "CountMinSketch":
        raise NotImplementedError


def heavy_hitters(stream: Iterable[str], k: int, epsilon: float = 1e-4, delta: float = 0.01) -> list[tuple[str, int]]:
    raise NotImplementedError
