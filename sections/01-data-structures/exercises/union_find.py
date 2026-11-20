"""
Union-find (disjoint set union) from scratch
Topic: 01.07  |  Priority: P1

Problem
-------
Build sections 4 to 6 of the chapter: n items numbered 0..n-1, each one
starting in its own group. Two operations: "these two belong together"
(union) and "which group is this in?" (find).

    uf = UnionFind(6)
    uf.union(0, 1) -> True      # two different groups were merged
    uf.union(1, 2) -> True
    uf.union(0, 2) -> False     # already in the same group
    uf.connected(0, 2) -> True,  uf.connected(0, 3) -> False
    uf.components -> 4           # {0, 1, 2} {3} {4} {5}
    uf.group_size(1) -> 3

Requirements
------------
- Keep the parent pointers in a plain list called self.parent, where
  self.parent[x] == x exactly when x is the root (the leader) of its group.
  Read and write it through self.parent; don't copy it to another list.
  The tests swap in a list that counts reads.
- find(x): return the root of x's group, and compress the path you walked
  (point the nodes on it at the root; path halving or splitting also count).
- union(a, b): True if two different groups were merged, False if a and b
  were already together. Hang the smaller group's root under the bigger
  group's root (union by size), or use union by rank.
- connected(a, b) -> bool.  group_size(x) -> how many items are in x's group.
- components: a property, the current number of groups, in O(1).
- Target: O(alpha(n)) amortized per operation, effectively a constant.

What the tests measure
----------------------
- Tree height: the tests read self.parent directly after 16,383 unions in a
  row (union(i, i + 1), and again with union(i + 1, i)) and in a few other
  orders. Every item must be at most log2(n) = 14 steps from its root, which
  union by size or rank guarantees. Always hanging a's root under b's, or
  b's under a's, builds a chain 16,383 steps tall for one of the two orders.
- Path compression: they build 100 chains of 400 items each straight into
  self.parent, then call find on all 40,000 items in a random order while
  counting reads of self.parent. The budget is 40 reads per find: full
  compression uses about 8, path halving about 11, path splitting about 20.
  Without compression it's about 400 per find (half a chain, two reads per
  step, every time).
- 1,000,000 random unions and connected() calls on 1,000,000 items run under
  a 20 s cap (about a second in pure Python).

Before you code (say it out loud)
---------------------------------
1. Picture each group as a tree pointing up to its root. What makes a tree tall?
2. Why does union by size keep every item within log2(n) of its root?
   (Hint: what happens to the size of your group each time you get deeper?)
3. What does path compression do to the tree, physically? Why does it never
   need to update the sizes?
4. Why can a single find still cost about log2(n), even with both tricks?

Run:  pytest -k "union_find and not patterns"
"""


class UnionFind:
    def __init__(self, n: int):
        raise NotImplementedError

    def find(self, x: int) -> int:
        raise NotImplementedError

    def union(self, a: int, b: int) -> bool:
        raise NotImplementedError

    def connected(self, a: int, b: int) -> bool:
        raise NotImplementedError

    def group_size(self, x: int) -> int:
        raise NotImplementedError

    @property
    def components(self) -> int:
        raise NotImplementedError
