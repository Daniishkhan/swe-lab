"""
MST in disguise: clustering and the widest path
Topic: 02.09  |  Priority: P1

1. k_clusters(n, edges, k) -> (spacing, labels)
   n points, numbered 0..n-1, and a list of (u, v, d): the distance between
   points u and v (only some pairs are listed; the graph is connected).
   Split the points into exactly k non-empty groups so that the *spacing*,
   the smallest distance listed between two points in different groups, is
   as large as possible. Return that spacing and labels, a list where
   labels[i] == labels[j] means i and j are in the same group (any label
   values are fine). If k == 1 the spacing is math.inf. 1 <= k <= n.

       k_clusters(4, [(0, 1, 1), (2, 3, 2), (1, 2, 10), (0, 3, 12)], 2)
       -> (10, [0, 0, 1, 1])        # groups {0, 1} and {2, 3}; closest pair across is 10

   Idea: run Kruskal and stop when k groups are left (equivalently: build the
   MST and cut its k - 1 most expensive cables). The spacing is the cost of
   the next cable Kruskal would have taken. O(E log E).

2. widest_path(n, edges, s, t) -> capacity
   edges are (u, v, c): an undirected link with bandwidth c > 0. A path's
   bandwidth is its narrowest link. Return the largest bandwidth of any path
   from s to t, 0 if there is no path, and math.inf if s == t.

       widest_path(4, [(0, 1, 5), (1, 3, 2), (0, 2, 3), (2, 3, 4)], 0, 3) -> 3

   Idea: the maximum spanning tree contains a widest path between every pair.
   Run Kruskal from the *widest* link down and stop the moment s and t join.
   O(E log E). The test uses 200,000 links under a time cap, and the links
   are arranged so that "for each bandwidth, from the top, BFS to see if s
   reaches t" does one BFS per distinct bandwidth.

Before you code (say it out loud)
---------------------------------
1. Why does stopping Kruskal early give the best spacing? What would a
   better clustering have to do to the cable Kruskal is about to take?
2. Why does the maximum spanning tree hold a widest path? Use the cycle
   property with "narrowest" in place of "most expensive".
3. Where else does "the path in the MST minimizes its largest cable" help?

Run:  pytest -k mst_clustering
"""


def k_clusters(n: int, edges: list[tuple[int, int, float]], k: int) -> tuple[float, list[int]]:
    raise NotImplementedError


def widest_path(n: int, edges: list[tuple[int, int, float]], s: int, t: int) -> float:
    raise NotImplementedError
