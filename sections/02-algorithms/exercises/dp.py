"""
Dynamic programming: define the state, fill the table, read the answer
Topic: 02.07  |  Priority: P0  |  Chapter: concepts/dynamic-programming.html (exercises 4-8)

The tests hand you special numbers and strings that COUNT every time you use
them (comparisons, and for numbers also + and -). So a correct answer is not
enough: plain recursion that tries every possibility fails, because it uses
the input millions of times. Each budget below is generous for the DP and far
too small for brute force. Numbers match the exercise numbers in the chapter.

4. count_ways(coins, amount) -> int
   How many different ways can you make `amount` from coins of the given
   (distinct, positive) values? Each coin value can be used any number of
   times. ORDER DOES NOT MATTER: 1+2 and 2+1 are the same way. Making 0 has
   exactly one way (use no coins).
   count_ways([1, 2, 5], 5) == 4      # 5, 2+2+1, 2+1+1+1, 1+1+1+1+1
   Target: O(len(coins) * amount) time, O(amount) extra space.
   Budget: about 20 uses of a coin value per (coin, amount) pair.

5. best_knapsack(weights, values, capacity) -> tuple[int, list[int]]
   0/1 knapsack, but return the CHOICE as well as the value: (best total
   value, sorted list of the indices of the items you take). Each item is
   taken at most once; total weight must be <= capacity. Weights are positive
   ints, values are ints >= 0. If several choices tie, any one is fine.
   best_knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7) == (9, [1, 2])
   Target: O(n * capacity) time. The 1D trick from the chapter keeps only the
   values, so think about what you need to keep to walk back.
   Budget: about 10 uses of a weight or value per (item, capacity) pair.

6. longest_increasing_subsequence(nums) -> list[int]
   Return one longest STRICTLY increasing subsequence (the values, in order).
   A subsequence keeps the original order but may skip items. If there are
   several of the longest length, any one is fine.
   longest_increasing_subsequence([10, 9, 2, 5, 3, 7, 101, 18])
       -> a list of length 4, such as [2, 3, 7, 18] or [2, 5, 7, 101]
   Target: O(n log n). The test counts comparisons between numbers and
   allows 4 * n * log2(n) for n = 4,000. The O(n^2) DP does about 8 million.
   Careful: the tails list from the chapter is NOT itself a subsequence.

7. diff_lines(old, new) -> list[tuple[str, str]]
   A line diff, like `diff` or `git diff`. Return (op, line) pairs where op
   is " " (line kept), "-" (line only in old) or "+" (line only in new), such
   that reading the " " and "-" lines in order gives `old`, reading the " "
   and "+" lines in order gives `new`, and the number of "-" and "+" lines is
   as SMALL as possible (keep as many lines as you can). Any minimal diff is
   accepted.
   diff_lines(["a", "b", "c"], ["a", "c", "d"])
       == [(" ", "a"), ("-", "b"), (" ", "c"), ("+", "d")]
   Target: O(len(old) * len(new)) time. The test counts line comparisons
   (== and !=) and allows 3 per cell of the table.

8. min_cut_cost(length, cuts) -> int
   A stick of `length` must be cut at every position in `cuts` (distinct
   ints, 0 < cut < length, in any order). Each cut costs the length of the
   piece being cut at that moment. You choose the order of the cuts. Return
   the smallest total cost.
   min_cut_cost(7, [1, 3, 4, 5]) == 16
   Target: O(m^3) for m cuts. The test counts uses of the positions and
   allows 4 * (m + 2)^3 (about 950,000) for m = 60. Trying every order of
   the cuts is m!.
   Don't change the input list.

Before you code (say it out loud)
---------------------------------
For each one: the state in words ("dp[i][j] = ..."), the recurrence (what
was the last choice?), the base cases, the order you fill the table in,
where the answer is, and the cost (number of states x work per state).

Run:  python3 -m pytest -k dp
"""


def count_ways(coins: list[int], amount: int) -> int:
    raise NotImplementedError


def best_knapsack(weights: list[int], values: list[int], capacity: int) -> tuple[int, list[int]]:
    raise NotImplementedError


def longest_increasing_subsequence(nums: list[int]) -> list[int]:
    raise NotImplementedError


def diff_lines(old: list[str], new: list[str]) -> list[tuple[str, str]]:
    raise NotImplementedError


def min_cut_cost(length: int, cuts: list[int]) -> int:
    raise NotImplementedError
