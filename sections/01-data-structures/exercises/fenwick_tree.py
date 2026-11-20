"""
Fenwick tree (binary indexed tree)
Topic: 01.10  |  Priority: P2

Problem
-------
Build sections 7 and 8 of the chapter: a list of n numbers that supports
"add to one item" and "sum of a range" in O(log n) each, stored in one
array of n + 1 slots, where slot j (counting from 1) holds the sum of the
lowbit(j) items ending at item j, and lowbit(j) = j & -j.

The public interface counts items from 0, like a Python list. Inside, you
will want to count from 1 (section 8 shows why slot 0 is a trap).

    f = FenwickTree.from_list([5, 2, 9, 1, 4])
    f.prefix_sum(3)      -> 16        # 5 + 2 + 9, the first 3 items
    f.range_sum(1, 4)    -> 12        # 2 + 9 + 1, items 1, 2, 3
    f.add(2, -6)                      # the list is now [5, 2, 3, 1, 4]
    f.range_sum(0, 5)    -> 15
    f.find_prefix(8)     -> 2         # 5, 7, 10: the running total first reaches 8 at item 2

Requirements
------------
- FenwickTree(n): n items, all 0. len(f) is n.
- FenwickTree.from_list(values): build from a list in O(n), not n adds.
  Don't modify the caller's list.
- add(i, delta): item i += delta, O(log n). An i outside 0..n-1 raises
  IndexError (including negative i: no wrap-around like Python lists).
- prefix_sum(k): the sum of the first k items, items 0..k-1, for
  0 <= k <= n. prefix_sum(0) is 0. O(log n).
- range_sum(lo, hi): items lo..hi-1 (half-open, like a slice), for
  0 <= lo <= hi <= n. An empty range is 0. O(log n).
- find_prefix(target): assume every item is >= 0. Return the smallest
  index i with items[0] + ... + items[i] >= target, or n if the total of
  all items is less than target. O(log n): walk down the tree by powers of
  two (section 10), not a binary search that calls prefix_sum each step.
- Items only need +, - and comparisons, so don't call int() or float() on
  them. Your array may start as plain 0s.

What the tests measure
----------------------
They hand you numbers that count every +, - and comparison done on them:
- from_list on 32,768 items must cost under 3n operations (n adds cost
  about 8.5n, because each one walks a path);
- add and prefix_sum on 65,536 items must cost at most about log2 n + 2
  operations each (a plain list pays n for a sum; a list of running totals
  pays n for an add);
- range_sum at most about 2 log2 n + 4;
- find_prefix at most about 3 log2 n + 6 = 54 (a binary search that calls
  prefix_sum at every step costs about 100 at this size; the walk down
  costs about 25).
A 10 s cap per test catches loops that never end (look at index 0).

Before you code (say it out loud)
---------------------------------
1. Which items does slot 12 cover? Slot 13? Slot 16? Write them in binary.
2. Why does the prefix walk strip the lowest 1 bit, and the add walk add it?
3. Why does an add at item 0 loop forever if you forget to shift to 1-based?
4. How does from_list reach O(n)? (Hint: each slot j only has to pass its
   total on to one other slot.)

Run:  pytest -k fenwick_tree
"""


class FenwickTree:
    def __init__(self, n: int):
        raise NotImplementedError

    @classmethod
    def from_list(cls, values) -> "FenwickTree":
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def add(self, i: int, delta) -> None:
        raise NotImplementedError

    def prefix_sum(self, k: int):
        raise NotImplementedError

    def range_sum(self, lo: int, hi: int):
        raise NotImplementedError

    def find_prefix(self, target) -> int:
        raise NotImplementedError
