"""
Merge, insert and intersect intervals
Topic: 01.09  |  Priority: P1

Problem
-------
Sections 3 and 4 of the chapter. An interval is a pair (start, end) with
start < end, and it is half-open: [start, end) contains start but not end,
so (9, 10) and (10, 11) do not overlap. A list of "blocks" is sorted by
start, and its intervals neither overlap nor touch.

1. merge(intervals): the blocks covering the same time as the intervals.
   Intervals that overlap or touch become one block. The input can be in
   any order.

       merge([(8, 10), (1, 3), (2, 6), (15, 18), (6, 7)])
           -> [(1, 7), (8, 10), (15, 18)]

2. insert(blocks, new): blocks with one more interval merged in.

       insert([(1, 3), (6, 9), (12, 15)], (2, 7))  -> [(1, 9), (12, 15)]
       insert([(1, 3), (6, 9)], (4, 5))           -> [(1, 3), (4, 5), (6, 9)]

3. intersect(a, b): the time covered by both block lists, as blocks.

       intersect([(0, 2), (5, 10)], [(1, 5), (8, 12)])
           -> [(1, 2), (8, 10)]

Requirements
------------
- Return new lists of (start, end) tuples. Don't modify the caller's lists.
- Times only need comparisons (<, <=, ==, ...); they may not be numbers.
- merge: O(n log n). One sort, then one pass.
- insert: O(log n + k) comparisons, where k is the number of blocks the new
  interval touches. Find where it goes with binary search (bisect has a
  key= argument), then only look at the blocks it touches. Copying the
  untouched blocks into the new list is fine: it costs no comparisons.
- intersect: O(m + n), two pointers.

What the tests measure
----------------------
They wrap every time in an object that counts comparisons:
- merge on 2,000 intervals: under 4 n log2 n + 10 n comparisons (about
  110,000). Comparing every pair, or merging repeatedly until nothing
  changes, needs millions.
- insert into 100,000 blocks: under 3 log2 n + 3k + 12 comparisons (about
  65 for a typical insert). Scanning from the left costs up to 100,000, and
  "append, then merge again" costs at least n.
- intersect of two 1,000-block lists: under 6 (m + n) comparisons. Checking
  every pair of blocks costs over a million.

Before you code (say it out loud)
---------------------------------
1. merge: why sort by start and not by end? When the next interval starts
   inside the current block, why is the new end max(end, next_end) and not
   next_end?
2. insert: which blocks can the new interval touch, and how does binary
   search find the first one?
3. intersect: after you compare the two current blocks, which pointer moves,
   and why can the other block still matter?

Run:  pytest -k interval_merge
"""


def merge(intervals: list[tuple]) -> list[tuple]:
    raise NotImplementedError


def insert(blocks: list[tuple], new: tuple) -> list[tuple]:
    raise NotImplementedError


def intersect(a: list[tuple], b: list[tuple]) -> list[tuple]:
    raise NotImplementedError
