"""
Two pointers, sliding window, prefix sums
Topic: 02.04  |  Priority: P0

Problem
-------
1. longest_unique_substring(s): length of the longest substring with no
   repeated characters.
2. min_subarray_len(target, nums): length of the shortest contiguous subarray
   of positive integers whose sum is >= target, or 0 if none.
3. subarray_sum_equals_k(nums, k): number of contiguous subarrays summing to k.
   nums may contain negatives (so a sliding window does NOT work here: why?).

Requirements
------------
- All three in O(n).

Before you code (say it out loud)
---------------------------------
1. A window is a caterpillar: the right end eats, the left end lets go. When
   must the left end move?
2. Why do negative numbers break the window idea for problem 3?
3. Prefix sums: sum(i..j) = P[j+1] - P[i]. What do you store in a hash map?

Run:  pytest -k sliding_window
"""


def longest_unique_substring(s: str) -> int:
    raise NotImplementedError


def min_subarray_len(target: int, nums: list[int]) -> int:
    raise NotImplementedError


def subarray_sum_equals_k(nums: list[int], k: int) -> int:
    raise NotImplementedError
