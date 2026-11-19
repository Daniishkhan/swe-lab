"""
Heap patterns: top-k, k-way merge, job scheduling
Topic: 01.04  |  Priority: P0

Problem
-------
Sections 8 to 10 of the chapter. You may use heapq's heappush, heappop,
heapify, heapreplace and heappushpop (or your MinHeap), but not
heapq.nlargest, heapq.nsmallest or heapq.merge: those are the answers.

1. top_k(stream, k): the k largest items of an iterable you can only walk
   once, sorted largest first. Fewer than k items: return them all, sorted
   largest first.

       top_k(iter([4, 9, 1, 7, 3, 8]), 3) -> [9, 8, 7]

2. merge_sorted(iterables): a generator that yields every item of k sorted
   iterables, in sorted order, pulling items lazily.

       list(merge_sorted([iter([1, 4, 9]), iter([2, 3]), iter([])]))
           -> [1, 2, 3, 4, 9]

3. assign_jobs(durations, workers): workers are numbered 0..workers-1 and
   all free at time 0. Jobs are taken in order; each goes to the worker who
   becomes free soonest (ties: the lowest worker number) and starts the
   moment that worker is free. Return a list of (worker, start_time), one
   per job.

       assign_jobs([1, 2, 3, 4, 5], 2)
           -> [(0, 0), (1, 0), (0, 1), (1, 2), (0, 4)]

Requirements
------------
- top_k: O(n log k) time and O(k) memory. Never hold the whole stream.
  Items only need `<`. Once k items are kept, an item that doesn't beat the
  smallest of them must cost exactly one comparison (section 8: compare
  with the root before touching the heap).
- merge_sorted: O(N log k) for N items in total, O(k) memory. Before yielding
  its m-th item, it must not have pulled more than k + m items in total, so
  a never-ending input works. Items only need `<`.
- assign_jobs: O(n log w) for n jobs and w workers.

What the tests measure
----------------------
- top_k: 100,000 counting items from a generator; comparisons must stay
  under 3 per item (sorting needs about 17, and "push, then pop if over k"
  about 13) and peak memory under 1 MB (keeping every item needs about
  8 MB). A rising stream, where every item gets in, must cost under
  3 log2 k per item (re-scanning a plain list of k costs k).
- merge_sorted: items pulled after each yield, and comparisons for 256
  lists: under 3 log2 k + 8 = 32 per item (scanning every front costs 256;
  a heap about 18 to 20).
- assign_jobs: 1,000,000 jobs on 500,000 workers under a 5 s cap.
  Scanning the workers for each job is 5 * 10^11 steps, and a sorted list
  with insort and pop(0) moves about as many items.

Before you code (say it out loud)
---------------------------------
1. top_k: why a *min*-heap for the k *largest*? What does one comparison
   with the root decide?
2. merge_sorted: what's in the heap at any moment, and how do you know which
   list to pull from next? What breaks a tie between equal items?
3. assign_jobs: what goes in the heap, and why does the worker number belong
   in the tuple?

Run:  pytest -k heap_patterns
"""

from collections.abc import Iterable, Iterator


def top_k(stream: Iterable, k: int) -> list:
    raise NotImplementedError


def merge_sorted(iterables: list[Iterable]) -> Iterator:
    raise NotImplementedError


def assign_jobs(durations: list[int], workers: int) -> list[tuple[int, int]]:
    raise NotImplementedError
