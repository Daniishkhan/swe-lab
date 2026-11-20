"""
An interval tree: a BST that remembers how far right each subtree reaches
Topic: 01.09  |  Priority: P1

Problem
-------
Section 8 of the chapter. Store intervals so that "which stored intervals
overlap [start, end)?" doesn't look at all of them. Intervals are half-open
pairs (start, end) with start < end; two overlap when
a.start < b.end and b.start < a.end.

    t = IntervalTree([(5, 20), (10, 30), (12, 15), (17, 19), (30, 40)])
    sorted(t.overlapping(14, 16))  -> [(5, 20), (10, 30), (12, 15)]
    t.add(15, 16)
    sorted(t.overlapping(14, 16))  -> [(5, 20), (10, 30), (12, 15), (15, 16)]
    t.overlapping(40, 50)           -> []
    len(t)                          -> 6

Requirements
------------
- A binary search tree keyed by start. Every node also stores max_end: the
  largest end anywhere in its subtree (itself included).
- IntervalTree(intervals): build a *balanced* tree from any iterable in
  O(n log n): sort by start, make the middle interval the root, and build
  each half the same way. Don't modify the caller's list.
- add(start, end): an ordinary BST insert (equal starts go right) that
  raises max_end on every node it passes. O(height). You don't need to
  rebalance: the tests add in random order. Duplicates are kept.
- overlapping(start, end): every stored interval that overlaps
  [start, end), as (start, end) tuples, in any order, duplicates included.
  Skip a whole subtree whenever it can't hold an answer:
    * its max_end <= start: everything in it ends too early;
    * a node's start >= end: that node and its whole right subtree start
      too late.
- len(t): how many intervals are stored.
- Times only need comparisons. No sorting inside overlapping().

What the tests measure
----------------------
They wrap every time in an object that counts comparisons, and use 20,000
intervals:
- each overlapping() call that returns k intervals must stay under
  6 (k + 1) log2 n comparisons (about 86 when k = 0). Scanning all n costs
  40,000. A tree that prunes with only one of the two rules above visits
  most of the nodes on some queries, so it fails too: queries near the left
  edge need the start rule, queries near the right edge need the max_end
  rule.
- building from intervals that are already sorted must give a balanced
  tree: queries on it get the same budget. Building by n adds in sorted
  order makes a chain n deep and fails.
- 20,000 add() calls in random order: under 6 n log2 n comparisons in total.

Before you code (say it out loud)
---------------------------------
1. Why is "sorted by start" alone not enough to find everything that covers
   a time t? Give a stored interval that a scan from the left would miss if
   it stopped early.
2. What does max_end let you skip, and why is that safe?
3. Which nodes' max_end can change when you add an interval, and which
   can't?
4. A rotation in a balanced tree moves two nodes. How would you fix their
   max_end values, and what does it cost?

Run:  pytest -k interval_tree
"""


class IntervalTree:
    def __init__(self, intervals=()):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def add(self, start, end) -> None:
        raise NotImplementedError

    def overlapping(self, start, end) -> list[tuple]:
        raise NotImplementedError
