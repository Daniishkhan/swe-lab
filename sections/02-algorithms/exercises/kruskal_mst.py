"""
Kruskal's minimum spanning tree
Topic: 02.09  |  Priority: P1

Problem
-------
n towns, numbered 0..n-1, and a list of possible cables. Each cable is a
tuple (u, v, w): it joins towns u and v (both ways) and costs w. Pick a set
of cables that connects every town, directly or through others, for the
lowest total cost. That set is a minimum spanning tree (MST).

    kruskal_mst(4, [(0, 1, 1), (1, 2, 2), (0, 2, 3), (2, 3, 4)])
    -> [(0, 1, 1), (1, 2, 2), (2, 3, 4)]        # total 7; (0, 2, 3) closes a loop

Requirements
------------
- kruskal_mst(n, edges) -> list of the chosen cables, each one exactly as it
  appears in `edges` (same tuple, same u/v order). Any order of the list is fine.
  The list has n - 1 cables and their total cost is as small as possible.
- Raise ValueError if the towns can't all be connected (the graph is
  disconnected). n = 1 gives [].
- The input can contain parallel cables (two cables between the same pair,
  different costs), self-loops (u == v) and equal costs. Costs are integers
  and may be zero or negative.
- Don't change the caller's `edges` list (sort a copy, or sort indexes).
- O(E log E): one sort, then near-constant work per cable. Write a small
  union-find (union by size + path compression) inside this file; it's the
  one from chapter 01.07. The test runs 300,000 cables on 100,000 towns
  under a time cap: a "search the tree built so far for a path from u to v"
  check per cable (BFS or DFS) is far too slow.

Before you code (say it out loud)
---------------------------------
1. Why is skipping a cable whose ends are already connected always safe?
   (Which property, and what does the loop look like?)
2. Why is taking the cheapest cable between two different groups always
   safe? Name the cut.
3. Why is "take the n - 1 cheapest cables" wrong? Give a 4-town example.
4. You can stop early. When?

Run:  pytest -k kruskal_mst
"""


def kruskal_mst(n: int, edges: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    raise NotImplementedError
