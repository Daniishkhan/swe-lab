"""
Two pointers, sliding windows, prefix sums: stop redoing work
Topic: 02.04  |  Priority: P0  |  Chapter: concepts/two-pointers-sliding-window.html (exercises 4-9)

Every problem here has an obvious solution that looks at every pair (i, j),
or every range nums[i..j]. That's O(n^2). Each one also has an O(n) or
O(n log n) solution that reuses work between neighbouring ranges. The tests
MEASURE the work, so a correct but quadratic answer fails:

  - text inputs are a read-only sequence that counts every character you read
    (indexing, slicing, for-loops). Use len(), s[i], s[i:j] and for-loops on
    it; it has no string methods. Read from it as you go: don't copy it first.
  - number inputs are special numbers that count every + and - done with them,
    and every comparison (about 40 per number allowed: enough to sort). What
    + and - give back is counted the same way, so copying the list or building
    your own running totals doesn't hide the work.
  - dedupe_sorted gets a fixed-size array that counts reads and writes and
    measures extra memory.

Numbers below match the exercise numbers in the chapter.

4. count_pairs_at_most(nums, limit) -> int
   Count pairs i < j with nums[i] + nums[j] <= limit. nums is NOT sorted and
   may hold duplicates and negatives. Don't change the input list (sorting a
   copy is fine). [3, 1, 5, 2], limit 6 -> 4.
   Target: O(n log n) time, and at most 3n additions/subtractions on the
   numbers (checking every pair needs about n^2 / 2).
   Hint: when a pair is small enough, how many OTHER pairs do you know are
   small enough without adding them up?

5. dedupe_sorted(nums, keep) -> int
   nums is sorted ascending. Rearrange it IN PLACE so that each value appears
   at most `keep` times (keep >= 1), in sorted order, in nums[:k]. Return k.
   What's left after position k doesn't matter. Don't delete, insert or
   append: only read and write by index.
   [1, 1, 1, 2, 2, 3], keep=2 -> 5, and nums[:5] == [1, 1, 2, 2, 3].
   Target: O(n) time (at most 4 reads and 1 write per item) and O(1) extra
   memory: no copy of the list, no dict, no set.

6. anagram_starts(text, pattern) -> list[int]
   Every start index i where text[i : i + len(pattern)] is a rearrangement
   of pattern, in increasing order. pattern has at least one character.
   "cbaebabacd", "abc" -> [0, 6].
   Target: O(n + m). The test allows about 5 reads per character of text
   and of pattern; re-checking every window from scratch needs n * m.

7. longest_k_distinct(s, k) -> int
   Length of the longest substring of s with at most k distinct characters
   (k >= 0). "eceba", k=2 -> 3 ("ece").
   Target: O(n). The test allows about 6 reads per character; trying every
   start position needs about n^2 / 2.

8. shortest_reaching(nums, target) -> int
   nums holds POSITIVE integers. Length of the shortest contiguous subarray
   whose sum is >= target (target >= 1), or 0 if there isn't one.
   [2, 3, 1, 2, 4, 3], target 7 -> 2 ([4, 3]).
   Target: O(n), at most 3n additions/subtractions.

9. count_sum_k(nums, k) -> int
   Number of contiguous, non-empty subarrays whose sum is exactly k. nums may
   hold NEGATIVE numbers and zeros, so a sliding window gives wrong answers
   here (section 7 says why). [1, -1, 0], k=0 -> 3.
   Target: O(n), at most 3n additions/subtractions.

Before you code (say it out loud)
---------------------------------
For each one: what's the brute force and its cost? Which pairs or ranges
does the fast version never look at, and why is it safe to skip them? Which
pointer moves, and why can't it ever need to move back?

Run:  python3 -m pytest -k sliding_window
"""


def count_pairs_at_most(nums: list, limit: int) -> int:
    raise NotImplementedError


def dedupe_sorted(nums, keep: int) -> int:
    raise NotImplementedError


def anagram_starts(text, pattern) -> list[int]:
    raise NotImplementedError


def longest_k_distinct(s, k: int) -> int:
    raise NotImplementedError


def shortest_reaching(nums: list, target: int) -> int:
    raise NotImplementedError


def count_sum_k(nums: list, k: int) -> int:
    raise NotImplementedError
