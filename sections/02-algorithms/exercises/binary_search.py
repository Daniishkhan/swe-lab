"""
Binary search and "search on the answer"
Topic: 02.03  |  Priority: P0

Problem
-------
1. lower_bound(nums, target): first index i where nums[i] >= target in a sorted
   list, or len(nums) if there is none. (No bisect module.)
2. min_ship_capacity(weights, days): packages must ship in order; each day the
   ship carries a contiguous run of packages whose total weight is at most the
   capacity. Return the smallest capacity that ships everything in `days` days.

Requirements
------------
- lower_bound in O(log n).
- min_ship_capacity in O(n log(sum(weights))).

Before you code (say it out loud)
---------------------------------
1. State your loop invariant: what is true about lo and hi on every iteration?
2. Half-open [lo, hi) or closed [lo, hi]? Pick one and stick to it.
3. For the shipping problem: why is "can we ship with capacity C?" monotonic
   in C? That monotonicity is what makes binary search legal.

Run:  pytest -k binary_search
"""


def lower_bound(nums: list[int], target: int) -> int:
    raise NotImplementedError


def min_ship_capacity(weights: list[int], days: int) -> int:
    raise NotImplementedError
