"""
Sorts from scratch: write the sorts, and prove how much work they do
Topic: 02.02  |  Priority: P0  |  Chapter: concepts/sorting.html (exercises 4-9)

The tests hand you special items that COUNT every comparison (<, <=, >, >=, ==).
So it's not enough to get the right order: a sort that does too many
comparisons fails. Don't call sorted(), list.sort(), heapq or bisect anywhere
in this file; the whole point is to build these yourself.

1. insertion_sort(items) -> None
   Sort the list IN PLACE. Stable. Must be fast on nearly-sorted input:
   a list with only a few items out of place should take about n comparisons,
   not n^2 / 2.

2. merge_sort(items) -> list
   Return a NEW sorted list (leave the input alone). Stable: when two items
   are equal, the one that came first stays first. At most n * log2(n)
   comparisons.

3. quicksort(items) -> None
   Sort IN PLACE with a RANDOM pivot (use the random module). Must stay fast
   on input that's already sorted AND on input where every item is equal.
   Hint: the "every item is equal" case breaks the simple version.
   Section 4's "Go deeper" box explains why and how to fix it.

4. counting_sort(items, key, max_key) -> list
   key(item) returns an int in [0, max_key]. Return a NEW list sorted by key,
   stable, in O(n + max_key) time. You may not compare items at all: the test
   gives you items that raise an error if you try.

5. merge_intervals(intervals) -> list[tuple[int, int]]
   Given (start, end) pairs in any order, merge the ones that overlap or touch
   and return them sorted by start. You MAY write your own sort for this or
   reuse merge_sort above. [(1, 3), (2, 6), (8, 10)] -> [(1, 6), (8, 10)].

6. kth_smallest(items, k) -> item
   The k-th smallest item, k counted from 1. Use quickselect (partition like
   quicksort, but only recurse into ONE side). Average O(n). The test allows
   about 10n comparisons; sorting the whole list needs more than that.

Before you code (say it out loud)
---------------------------------
For each sort: its best, average and worst case; whether it's stable; and how
much extra memory it uses.

Run:  python3 -m pytest -k sorts
"""
import random  # noqa: F401  (you'll want it for quicksort and quickselect)


def insertion_sort(items: list) -> None:
    raise NotImplementedError


def merge_sort(items: list) -> list:
    raise NotImplementedError


def quicksort(items: list) -> None:
    raise NotImplementedError


def counting_sort(items: list, key, max_key: int) -> list:
    raise NotImplementedError


def merge_intervals(intervals: list) -> list:
    raise NotImplementedError


def kth_smallest(items: list, k: int):
    raise NotImplementedError
