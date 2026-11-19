"""
Binary min-heap, plus two classic uses
Topic: 01.04  |  Priority: P0

Problem
-------
1. MinHeap backed by a Python list (no heapq inside the class).
2. top_k_frequent: the k most frequent values.
3. merge_k_sorted: merge k sorted lists into one sorted list.
   (You may use your MinHeap or heapq here; try both.)

Requirements
------------
- push(x), pop() -> smallest, peek() -> smallest, len(h).
- pop/peek on an empty heap raise IndexError.
- MinHeap.from_list(items) builds a heap in O(n), not O(n log n).
- top_k_frequent(nums, k): any order; O(n log k).
- merge_k_sorted(lists): O(N log k) where N is the total number of items.

Before you code (say it out loud)
---------------------------------
1. Where are the children of index i? The parent?
2. Why is bottom-up heapify O(n)? (Hint: most nodes are near the bottom.)
3. For top-k, why keep a heap of size k instead of sorting?

Run:  pytest -k min_heap
"""


class MinHeap:
    def __init__(self):
        raise NotImplementedError

    @classmethod
    def from_list(cls, items) -> "MinHeap":
        raise NotImplementedError

    def push(self, x) -> None:
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError

    def peek(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


def top_k_frequent(nums: list, k: int) -> list:
    raise NotImplementedError


def merge_k_sorted(lists: list[list]) -> list:
    raise NotImplementedError
