"""
Dynamic programming classics
Topic: 02.07  |  Priority: P0

Problem
-------
1. edit_distance(a, b): minimum insertions, deletions, substitutions to turn
   a into b.
2. lis_length(nums): length of the longest strictly increasing subsequence.
3. knapsack_01(weights, values, capacity): max total value with total weight
   <= capacity, each item used at most once.

Requirements
------------
- edit_distance: O(len(a) * len(b)) time; then try O(min(len)) space.
- lis_length: O(n^2) first, then O(n log n) with patience sorting.
- knapsack_01: O(n * capacity); then try a 1D array (why iterate backwards?).

Before you code (say it out loud)
---------------------------------
1. Define the state in words: "dp[i][j] = ..."
2. Write the recurrence and base cases before any code.
3. Top-down (memo) or bottom-up (table)? Trade-offs?

Run:  pytest -k dp
"""


def edit_distance(a: str, b: str) -> int:
    raise NotImplementedError


def lis_length(nums: list[int]) -> int:
    raise NotImplementedError


def knapsack_01(weights: list[int], values: list[int], capacity: int) -> int:
    raise NotImplementedError
