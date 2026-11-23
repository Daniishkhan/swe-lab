"""
Hash map patterns: seen before, group by key, prefix sums
Topic: 01.01  |  Priority: P0

Problem
-------
Three classic problems where a hash map turns an O(n^2) search into O(n).
Each matches a pattern from section 11 of the chapter.

1. two_sum(nums, target) -> (i, j) or None
   Indices i < j with nums[i] + nums[j] == target. If several pairs work,
   return the one with the smallest j, and for that j the smallest i.
   None if there is no pair.
       two_sum([2, 7, 11, 15], 9)   -> (0, 1)
       two_sum([3, 3], 6)           -> (0, 1)

2. group_anagrams(words) -> list[list[str]]
   Group words that are rearrangements of each other. Groups appear in the
   order their first word appears; words keep their input order.
       group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
       -> [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]

3. subarray_sum_count(nums, k) -> int
   How many contiguous, non-empty slices nums[i:j] sum to exactly k.
   Numbers may be negative or zero, so a sliding window doesn't work.
       subarray_sum_count([1, 1, 1], 2)      -> 2
       subarray_sum_count([1, -1, 1, -1], 0) -> 4

Requirements
------------
- Targets: two_sum O(n) average; group_anagrams O(n * k log k) for words of
  length up to k (O(n * k) is possible); subarray_sum_count O(n) average.
  All O(n) extra space.

What the tests measure
----------------------
They pass a list that counts every read (indexing and iteration) and fails
past a few reads per item. Comparing every pair reads about n^2 / 2 times.
Each test also has a 5-second limit, so a pair loop over a copy, a list of
groups or a prefix-sum list fails too.

Before you code (say it out loud)
---------------------------------
1. two_sum: what exactly do you look up for each number, and what do you
   store? Why look up before storing (think of [5, 1] with target 10)?
2. group_anagrams: what label is equal for "eat" and "tea" but not "tan"?
   Why can't the label be a list?
3. subarray_sum_count: if the prefix sums are P[i] and P[j], what is the sum
   of nums[i:j]? So what do you count in the map, and what's in it before
   you read the first number?

Run:  pytest -k hash_patterns
"""


def two_sum(nums, target):
    raise NotImplementedError


def group_anagrams(words):
    raise NotImplementedError


def subarray_sum_count(nums, k):
    raise NotImplementedError
