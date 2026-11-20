"""
Prim's minimum spanning tree: with a heap (sparse) and with an array (dense)
Topic: 02.09  |  Priority: P1

Problem
-------
Grow one tree from town 0. At every step, add the cheapest cable that leaves
the tree (one end inside, one end outside). That cable is safe by the cut
property, with the cut "tree | everything else".

1. prim_mst(n, adj) -> (total, parent)
   adj[u] is a list of (v, w) pairs: a cable from u to v costing w. The graph
   is undirected, so every cable appears twice: in adj[u] and in adj[v].
   Return the MST's total cost and a parent list: parent[0] = -1, and for
   every other town, parent[v] is the town it was attached from (so the tree's
   cables are (parent[v], v) for v = 1..n-1). Raise ValueError if some town
   can't be reached. n = 1 gives (0, [-1]).

       adj = [[(1, 4), (2, 1)], [(0, 4), (2, 2)], [(0, 1), (1, 2)]]
       prim_mst(3, adj) -> (3, [-1, 2, 0])

   Target: O(E log V) with heapq. Read each adjacency entry about once (when
   its town joins the tree). The test hands you an adjacency list that counts
   every entry you read, with a budget of about 2 reads per entry: a version
   that rescans every cable of the tree at each step reads V * E entries.
   Stale heap entries (a town that already joined) are skipped when popped.

2. prim_dense(n, dist) -> (total, parent)
   A complete graph: every pair of points can be joined, and dist(i, j) gives
   the cost (dist(i, j) == dist(j, i)). Same return value as prim_mst.
   There are about n^2 / 2 cables, so don't build an edge list or a heap of
   them. Keep one array best[v] = cheapest known cable from the tree to v,
   and at each step scan it for the smallest. O(n^2) time, O(n) extra memory.
   The test caps calls to dist() at n^2 and peak extra memory at a small
   multiple of n.

Before you code (say it out loud)
---------------------------------
1. Prim and Dijkstra differ in one line. Which line, and what does each
   one put in the heap?
2. Why does the heap version get slower than the array version when every
   pair of towns has a cable? Do the arithmetic for n = 10,000.
3. What does Prim return if the graph is disconnected and you don't check?

Run:  pytest -k prim_mst
"""


def prim_mst(n: int, adj) -> tuple[int, list[int]]:
    raise NotImplementedError


def prim_dense(n: int, dist) -> tuple[float, list[int]]:
    raise NotImplementedError
