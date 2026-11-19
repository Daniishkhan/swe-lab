"""
Recursion and backtracking
Topic: 02.06  |  Priority: P0

Problem
-------
1. subsets(nums): all subsets of distinct integers.
2. permutations(nums): all orderings of distinct integers.
3. count_n_queens(n): number of ways to place n queens on an n x n board so
   no two attack each other.

Requirements
------------
- Output order does not matter for (1) and (2).
- For n-queens, prune with sets for columns and both diagonals.

Before you code (say it out loud)
---------------------------------
1. Draw the decision tree. What is a "choice" at each level?
2. Choose, explore, un-choose: where does the un-choose happen?
3. Complexity: how many leaves does each tree have (2^n, n!)?

Run:  pytest -k backtracking
"""


def subsets(nums: list[int]) -> list[list[int]]:
    raise NotImplementedError


def permutations(nums: list[int]) -> list[list[int]]:
    raise NotImplementedError


def count_n_queens(n: int) -> int:
    raise NotImplementedError
