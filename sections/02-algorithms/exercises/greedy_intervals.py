"""
Greedy on intervals: stab them all, cover a range
Topic: 02.10  |  Priority: P1

Problem
-------
Section 3 of the chapter proved "sort by end, take what fits" for the most
meetings in one room. These are its two cousins. Both are greedy, both are
O(n log n), and for both you should be able to say WHY the greedy is safe.

1. fewest_stabs(intervals): intervals are CLOSED, [start, end] with
   start <= end, like balloons on a line: an arrow shot at x pops every
   balloon with start <= x <= end, so touching counts. Return a list of
   points (values taken from the input) that stabs every interval, using
   as few points as possible. Return the points in increasing order.

       fewest_stabs([(10, 16), (2, 8), (1, 6), (7, 12)])  -> [6, 12]
       fewest_stabs([(1, 2), (3, 4), (5, 6), (7, 8)])     -> [2, 4, 6, 8]
       fewest_stabs([(1, 2), (2, 3)])                     -> [2]

   (Other point lists of the same size are also right: [6, 12] could be
   [6, 10]. The tests check that every interval is stabbed and that you
   used the fewest points.)

2. fewest_to_cover(clips, T): clips are (start, end) with start < end. Pick
   the fewest clips whose union covers all of [0, T] (T > 0). Touching is
   enough: (0, 4) and (4, 7) cover [0, 7]. Return the indices of the clips
   you picked, in any order, or None if [0, T] can't be covered.

       fewest_to_cover([(0, 2), (4, 6), (8, 10), (1, 9), (1, 5), (5, 9)], 10)
           -> [0, 3, 2]          # (0, 2) + (1, 9) + (8, 10)
       fewest_to_cover([(0, 1), (1, 2)], 5)  -> None
       fewest_to_cover([(-3, 8)], 5)         -> [0]

Requirements
------------
- Don't modify the caller's list. Empty input: fewest_stabs([]) -> [];
  fewest_to_cover([], T) -> None.
- Values only need comparisons (<, <=, ==, max, min). No arithmetic.
- Both functions: O(n log n). Sort once, then one pass.

What the tests measure
----------------------
Every value is wrapped in an object that counts comparisons.
- Both functions on 2,000 intervals with answers of 200 to 400 points or
  clips: under 3 n log2 n + 10 n comparisons (about 86,000). Sorting once
  and walking once needs about 25,000 to 45,000. Re-scanning the intervals
  each time you place a point or pick a clip needs 400,000 or more.
- Optimality: against brute force (every subset) on small inputs, and on
  big inputs built so that the right answer is known.

Before you code (say it out loud)
---------------------------------
1. fewest_stabs: which interval must your first arrow hit, and where is the
   best place to shoot it? Why can't a different first arrow do better?
2. fewest_stabs: what does a set of k intervals that don't touch each other
   tell you about every possible answer? (That's the proof certificate.)
3. fewest_to_cover: you have covered [0, reach]. Which clips are allowed
   next, and which one do you take? Prove it with "greedy stays ahead".
4. What do you return when no clip starts at or before reach?

Run:  pytest -k greedy_intervals
"""


def fewest_stabs(intervals: list[tuple]) -> list:
    raise NotImplementedError


def fewest_to_cover(clips: list[tuple], T) -> list[int] | None:
    raise NotImplementedError
