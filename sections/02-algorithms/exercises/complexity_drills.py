"""
Complexity drills: code whose tests measure how much work it does
Topic: 02.01  |  Priority: P0  |  Chapter: concepts/complexity.html (exercises 4-7)

These tests don't just check the answer. They count steps (copies, reads,
multiplications), so a correct but slow solution FAILS. That's the point:
complexity is something you can measure, not just claim.

1. has_duplicate(nums) -> bool
   True if any value appears twice. Target: O(n) time, O(n) extra space.

2. DynamicArray
   A growable array built on a fixed-size Python list (the "block").
   - append(x): if the block is full, allocate a block twice as big and copy
     every existing item into it. Add 1 to self.copies for EACH item copied.
   - __getitem__(i), __len__(), and a `capacity` property.
   - Start with capacity 1. Do not use list.append on the block itself; write
     into slots: self._block[self._size] = x.
   Target: n appends cause fewer than 2n copies (amortized O(1) per append).
   Experiment: grow by +10 instead of x2 and watch the test fail.

3. count_pairs_with_sum(sorted_nums, target) -> int
   sorted_nums is sorted ascending with DISTINCT values. Count pairs i < j
   with sorted_nums[i] + sorted_nums[j] == target.
   Target: O(n) with two pointers. The test passes a list that counts reads;
   more than about 2n reads fails.

4. fast_power(base, exp) -> (result, multiplications)
   base ** exp for integer exp >= 0, using square-and-multiply. Count every
   `*` you perform between numbers. Don't use ** or pow().
   Target: O(log exp) multiplications (at most 2 * log2(exp) + 2).

Before you code (say it out loud)
---------------------------------
For each one: what's the brute force, what's its complexity, and what's the
one idea that makes it faster?

Run:  python3 -m pytest -k complexity_drills
"""


def has_duplicate(nums: list) -> bool:
    raise NotImplementedError


class DynamicArray:
    def __init__(self):
        raise NotImplementedError

    @property
    def capacity(self) -> int:
        raise NotImplementedError

    def append(self, x) -> None:
        raise NotImplementedError

    def __getitem__(self, i):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


def count_pairs_with_sum(sorted_nums, target: int) -> int:
    raise NotImplementedError


def fast_power(base: int, exp: int) -> tuple[int, int]:
    raise NotImplementedError
