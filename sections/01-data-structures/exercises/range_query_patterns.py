"""
Range query patterns: count smaller after, add to a whole range
Topic: 01.10  |  Priority: P2

Problem
-------
Sections 9 and 10 of the chapter. You may import your FenwickTree or
SegmentTree from the other exercises, or write the few lines you need
here.

1. count_smaller_after(nums): for every i, how many items to the right of
   i are strictly smaller than nums[i].

       count_smaller_after([5, 2, 6, 1]) -> [2, 1, 1, 0]
       # right of 5: 2 and 1 are smaller. Right of 2: 1. Right of 6: 1.

   nums are any ints, including negatives and values up to 10**18, so you
   can't use the values themselves as indexes: squash them to ranks first
   (coordinate compression, section 10).

2. RangeAdder(n): n items, all 0.
       add(lo, hi, delta): add delta to every item lo..hi-1 (half-open).
       get(i): the current value of item i.

       r = RangeAdder(5)
       r.add(1, 4, 10)        # [0, 10, 10, 10, 0]
       r.add(0, 2, -3)        # [-3, 7, 10, 10, 0]
       r.get(1) -> 7,  r.get(4) -> 0

Requirements
------------
- count_smaller_after: O(n log n) time. Return a new list.
- RangeAdder: add and get in O(log n) each, however wide the range.
  0 <= lo <= hi <= n (an empty range changes nothing), 0 <= i < n.
  delta values only need + and - (don't call int() on them).

What the tests measure
----------------------
- count_smaller_after: 100,000 random values under a 10 s cap. A Fenwick
  tree over ranks takes under a second in pure Python; comparing every
  pair is 5 * 10**9 comparisons, about two minutes in Python.
- RangeAdder: deltas that count every + and -. On 65,536 items, add must
  cost at most 2 log2 n + 6 operations and get at most log2 n + 3 (about
  38 and 19). Looping over the range costs about n/4, about 16,000 per
  add; a plain difference array makes get cost about n/2.

Before you code (say it out loud)
---------------------------------
1. count_smaller_after: why walk from the right? What does the Fenwick tree
   count, and which prefix sum answers "how many seen so far are smaller"?
2. Why do duplicates need care: is an equal value "smaller"?
3. RangeAdder: "add delta to a whole range" becomes two point changes in a
   difference array. Which two, and why is get(i) then a prefix sum?
4. A sorted list with bisect.insort also answers question 1. What does it
   cost per insert, and why is it still fast at 100,000 but not at 10**7?

Run:  pytest -k range_query_patterns
"""


def count_smaller_after(nums: list[int]) -> list[int]:
    raise NotImplementedError


class RangeAdder:
    def __init__(self, n: int):
        raise NotImplementedError

    def add(self, lo: int, hi: int, delta) -> None:
        raise NotImplementedError

    def get(self, i: int):
        raise NotImplementedError
