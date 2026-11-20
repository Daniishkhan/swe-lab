"""
Binary search: boundaries, rotated arrays, and search on the answer
Topic: 02.03  |  Priority: P0  |  Chapter: concepts/binary-search.html (exercises 4-7)

The tests COUNT your work. Sorted lists come as read-only sequences that count
every item you read (nums[i], iterating, slicing), and numbers come as ints
that count every comparison and every + or - done with them. So the right
answer isn't enough: a solution that reads or computes too much fails, even if
it's correct. Don't use the bisect module (the point is to write the loop
yourself), and don't copy the input into a plain list to dodge the counting.
Numbers below match the exercise numbers in the chapter.

4. search_range(nums, target) -> tuple[int, int]
   nums is sorted ascending and may hold duplicates. Return (first, last): the
   first and last index holding target, or (-1, -1) if it isn't there.
   [5, 7, 7, 8, 8, 10], 8 -> (3, 4)      [5, 7, 7, 8, 8, 10], 6 -> (-1, -1)
   O(log n) reads, even when EVERY item equals target: finding one copy and
   walking outward is O(n). The test allows 6 * ceil(log2(n + 1)) + 6 reads
   (108 for n = 100,000).
   nums supports len(), nums[i] and iteration; it has no list methods.

5. search_rotated(nums, target) -> int
   nums was sorted ascending (all values distinct), then rotated: cut in two
   and the pieces swapped, so [0, 1, 2, 4, 5, 6, 7] might arrive as
   [4, 5, 6, 7, 0, 1, 2]. It may not be rotated at all. Return the index of
   target, or -1. O(log n) reads: the test allows 8 * ceil(log2(n + 1)) + 8
   (144 for n = 100,000).

6. min_ship_capacity(weights, days) -> int
   Packages ship in the given order. Each day the ship loads the next packages
   in line, as many as fit: their total weight can't go over its capacity.
   Return the smallest capacity that ships everything within `days` days.
   weights is non-empty, every weight >= 1, days >= 1.
   [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], days=5 -> 15
   (day loads: [1, 2, 3, 4, 5], [6, 7], [8], [9], [10]).
   O(n log(sum of weights)). Trying capacities one at a time fails the test,
   which allows 4 * n * (ceil(log2(sum of weights)) + 2) counted operations.

7. max_min_gap(positions, k) -> int
   positions: distinct integers, in any order (house numbers on a long road).
   Put k sensors at k of these positions so that the SMALLEST distance between
   two sensors is as LARGE as possible, and return that distance.
   2 <= k <= len(positions).
   [1, 2, 8, 4, 9], k=3 -> 3   (sensors at 1, 4 and 8)
   Sort first (sorted() is fine here). O(n log n + n log(range)): the test
   allows 2 * n * log2(n) + 4 * n * (ceil(log2(range)) + 2) counted
   operations. Watch the direction: you want the LARGEST value that works.

Before you code (say it out loud)
---------------------------------
1. What is the yes/no question, and why can its answer flip only once?
2. What do lo and hi mean? Say the invariant before you write the loop.
3. What are the smallest and largest possible answers? Is hi a sure "yes",
   or one past the end meaning "none"?
4. Why does every branch make the range smaller? (That's why the loop ends.)

Run:  python3 -m pytest -k binary_search
"""


def search_range(nums, target: int) -> tuple[int, int]:
    raise NotImplementedError


def search_rotated(nums, target: int) -> int:
    raise NotImplementedError


def min_ship_capacity(weights: list[int], days: int) -> int:
    raise NotImplementedError


def max_min_gap(positions: list[int], k: int) -> int:
    raise NotImplementedError
