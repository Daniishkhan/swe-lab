"""
Monotonic stack and monotonic deque
Topic: 01.02  |  Priority: P0

Problem
-------
1. next_greater(nums): for each index, the next value to its right that is
   strictly greater, or -1 if there is none (section 7 of the chapter).

       next_greater([2, 1, 2, 4, 3]) -> [4, 2, 4, -1, -1]

2. sliding_window_max(nums, k): the max of every window of k consecutive
   values, left to right (section 7).

       sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) -> [3, 3, 5, 5, 6, 7]

Requirements
------------
- Both O(n) time, whatever k is. The obvious versions are O(n^2) and O(n*k):
  say them out loud first, then improve. A lazy heap for the window max is
  O(n log n) and passes these tests; the target is the O(n) deque.
- next_greater([]) is [].
- sliding_window_max returns [] if nums is empty; otherwise assume
  1 <= k <= len(nums).
- Only read nums by index or by iterating; don't modify it.

What the tests measure
----------------------
They pass a list that counts every read and fails past about 8 reads per
item, and a 5-second cap catches nested loops that run on a copy of the
list. Scanning right from every item, or taking max() of every window,
fails.

Before you code (say it out loud)
---------------------------------
1. Physical picture: people in a line, each looking right for someone
   taller. Which people are still waiting, and in what order are they?
2. What order does the stack keep (increasing or decreasing), and why does
   the question decide it?
3. Why is each index pushed once and popped at most once? Why is that O(n)?
4. For the window: why can a smaller, older value never be the max again
   once a bigger value arrives? Why a deque and not a stack?

Run:  pytest -k monotonic
"""


def next_greater(nums: list[int]) -> list[int]:
    raise NotImplementedError


def sliding_window_max(nums: list[int], k: int) -> list[int]:
    raise NotImplementedError
