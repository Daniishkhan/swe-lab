"""
Monotonic stack and monotonic deque
Topic: 01.02  |  Priority: P0

Problem
-------
1. next_greater(nums): for each index, the next value to the right that is
   strictly greater, or -1 if none.
2. sliding_window_max(nums, k): the max of every contiguous window of size k.

Requirements
------------
- Both in O(n). The naive versions are O(n^2) and O(n*k); write those first
  in your head, then improve.
- sliding_window_max returns [] if nums is empty; assume 1 <= k <= len(nums)
  otherwise.

Before you code (say it out loud)
---------------------------------
1. Physical picture: people in a line looking right. Who can a short person
   never block?
2. What invariant does the stack keep (increasing or decreasing)?
3. Why does each element get pushed and popped at most once (that is the O(n))?

Run:  pytest -k monotonic
"""


def next_greater(nums: list[int]) -> list[int]:
    raise NotImplementedError


def sliding_window_max(nums: list[int], k: int) -> list[int]:
    raise NotImplementedError
