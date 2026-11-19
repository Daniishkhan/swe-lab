"""
Union-find (disjoint set union)
Topic: 01.07  |  Priority: P1

Problem
-------
Track which of n elements (0..n-1) are in the same group as you union them.

Requirements
------------
- find(x) -> representative of x's set (use path compression).
- union(a, b) -> True if two different sets were merged, False if already joined
  (use union by rank or by size).
- connected(a, b) -> bool.
- `components` -> current number of disjoint sets.
- Target: near O(1) amortized (inverse Ackermann).

Before you code (say it out loud)
---------------------------------
1. Picture each set as a tree pointing to its root. What makes trees tall?
2. What does path compression do to the tree, physically?
3. Where does this show up: Kruskal's MST, connected components, network
   connectivity, "accounts merge".

Run:  pytest -k union_find
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

    @property
    def components(self) -> int:
        raise NotImplementedError
