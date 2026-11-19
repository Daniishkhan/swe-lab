"""
Sorts from scratch: write the sorts, and prove how much work they do
Topic: 02.02  |  Priority: P0  |  Chapter: concepts/sorting.html (exercises 4-9)

The tests hand you special items that COUNT every comparison (<, <=, >, >=, ==).
So it's not enough to get the right order: a solution that does too many
comparisons fails. Don't call sorted(), list.sort(), heapq or bisect anywhere
in this file; the whole point is to build these yourself. Numbers below match
the exercise numbers in the chapter.

4. merge_sort(items) -> list
   Return a NEW sorted list (leave the input alone, and return a new list even
   for 0 or 1 items). Stable: when two items are equal, the one that came first
   stays first. At most n * log2(n) comparisons. Avoid list.pop(0): it shifts
   every remaining item, a hidden O(n).

5. count_inversions(items) -> int
   An inversion is a pair i < j with items[i] > items[j] (equal items are NOT
   an inversion). It measures how unsorted a list is: insertion sort does
   about n + inversions work. Counting every pair is O(n^2); do it in
   O(n log n) by piggybacking on merge sort: while merging, when you take an
   item from the RIGHT pile, it jumps ahead of everything still in the left
   pile. Don't change the input list. At most n * log2(n) comparisons.

6. quicksort(items) -> None
   Sort IN PLACE with a RANDOM pivot (use the random module). Must stay fast
   on input that's already sorted AND on input where every item is equal.
   Hint: the "every item is equal" case breaks the simple (Lomuto) partition.
   Section 4's "Go deeper" box explains why and how to fix it.

7. counting_sort(items, key, max_key) -> list
   key(item) returns an int in [0, max_key]. Return a NEW list sorted by key,
   stable, in O(n + max_key) time. You may not compare items at all: the test
   gives you items that raise an error if you try. It also counts calls to
   key(): call it at most twice per item.

8. merge_intervals(intervals) -> list[tuple[int, int]]
   Given (start, end) pairs in any order, merge the ones that overlap or touch
   and return them sorted by start. You MAY reuse merge_sort above.
   [(1, 3), (2, 6), (8, 10)] -> [(1, 6), (8, 10)].
   Careful: the next interval may sit entirely inside the current one.

9. kth_smallest(items, k) -> item
   The k-th smallest item, k counted from 1. Use quickselect (partition like
   quicksort, but only keep going on ONE side). Average O(n). The test allows
   about 10n comparisons (best of 3 runs); sorting everything needs about 13n.
   Partition in ONE pass, comparing each item with the pivot at most twice:
   three separate list comprehensions cost 3 comparisons per item and can blow
   the budget. Must also be fast when many items are equal. Don't change the
   input list.

Before you code (say it out loud)
---------------------------------
For each one: its best, average and worst case; whether it's stable; and how
much extra memory it uses.

Run:  python3 -m pytest -k sorts
"""
import random  # noqa: F401  (you'll want it for quicksort and quickselect)


def merge_sort(items: list) -> list:
    raise NotImplementedError


def count_inversions(items: list) -> int:
    raise NotImplementedError


def quicksort(items: list) -> None:
    raise NotImplementedError


def counting_sort(items: list, key, max_key: int) -> list:
    raise NotImplementedError


def merge_intervals(intervals: list) -> list:
    raise NotImplementedError


def kth_smallest(items: list, k: int):
    raise NotImplementedError
