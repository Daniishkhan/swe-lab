"""
Segment tree for any combine (sum, min, max, ...)
Topic: 01.10  |  Priority: P2

Problem
-------
Build sections 4 and 5 of the chapter: a tree of partial answers over a
list, where each node holds the combined answer for one block of items
and the root holds the answer for the whole list.

combine(a, b) is any associative function: combine(combine(a, b), c) ==
combine(a, combine(b, c)). It is NOT necessarily commutative, so the order
matters: a query must combine items left to right. identity is the value
that changes nothing: combine(identity, x) == combine(x, identity) == x.

    t = SegmentTree([5, 2, 9, 1, 4], min, float("inf"))
    t.query(1, 4)   -> 1          # min(2, 9, 1), items 1, 2, 3
    t.update(3, 7)                # the list is now [5, 2, 9, 7, 4]
    t.query(2, 5)   -> 4

    s = SegmentTree(["a", "b", "c", "d"], lambda x, y: x + y, "")
    s.query(1, 4)   -> "bcd"      # left to right, not "dcb" or "cbd"

Requirements
------------
- SegmentTree(values, combine, identity): build in O(n), with fewer than
  2n calls to combine. values may be empty. len(t) is n.
- query(lo, hi): combine(items[lo], ..., items[hi-1]) for the half-open
  range lo..hi-1, 0 <= lo <= hi <= n. An empty range gives identity.
  O(log n) calls to combine.
- update(i, value): set item i to value (replace, not add). O(log n).
  An i outside 0..n-1 raises IndexError.
- Only call combine on items, never compare them or add them yourself.

What the tests measure
----------------------
They count every call to combine:
- building from 50,000 items: under 2n calls;
- 2,000 random queries on 50,000 items: at most 4 log2 n + 4 calls each,
  about 66. The recursive tree from section 4 needs about 27, a
  bottom-up one about 14. Reducing the slice costs about n/4, about
  12,500, and blocks of size sqrt(n) about 270.
- 2,000 updates: at most 2 log2 n + 4 calls each, about 35. A tree needs
  about 16; re-reducing a sqrt(n) block costs about 220, rebuilding all n.
Order is checked with string concatenation, which isn't commutative.

Before you code (say it out loud)
---------------------------------
1. Where do node i's children live in the array? Why size 2n or 4n?
2. A node's block is fully inside the query, fully outside, or partly
   inside. What do you do in each case?
3. Why does a query touch at most four nodes on each level (two of them
   partly inside)?
4. Where does identity come in, and what would go wrong for min if you
   used 0 instead of infinity?

Run:  pytest -k segment_tree
"""


class SegmentTree:
    def __init__(self, values, combine, identity):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def query(self, lo: int, hi: int):
        raise NotImplementedError

    def update(self, i: int, value) -> None:
        raise NotImplementedError
