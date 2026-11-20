"""
Dijkstra's shortest paths
Topic: 02.08  |  Priority: P1

Problem
-------
A directed graph with nodes 0..n-1 and edges (u, v, w): a one-way road from
u to v that takes w minutes, with w >= 0. Parallel edges and edges with
w = 0 can appear.

    edges = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]
    dijkstra(5, edges, 0)            ->  [0, 3, 1, 4, inf]
    shortest_route(5, edges, 0, 3)   ->  (4, [0, 2, 1, 3])

Functions
---------
dijkstra(n, edges, src) -> list
    dist[i] = the least total weight of a path from src to i, or math.inf
    if no path exists. dist[src] = 0.
    Target: O((V + E) log V) time with a binary heap (heapq), O(V + E) space.

shortest_route(n, edges, src, dst) -> (total, path) | None
    One cheapest path from src to dst, as (its total weight, [src, ..., dst]),
    or None if dst can't be reached. src == dst gives (0, [src]).
    Stop as soon as the answer for dst is final: on a big graph with dst
    close to src, the tests give you a budget far below the whole graph.

How the tests measure your work
-------------------------------
Every weight the tests pass in is a float subclass that counts how often it
is added to something. Each edge should be added in at most once or twice
(once when its start node is finalised, maybe twice if you compute
dist[u] + w in the `if` and again in the assignment). Use the weights as
they come (no float(w) or int(w) copies): the counting is how a Dijkstra
that re-expands stale heap entries, or a Bellman-Ford in disguise, gets
caught. A 60,000-node test also runs under a time cap, so scanning every
node to find the next one (O(V^2)) fails.

Before you code (say it out loud)
---------------------------------
1. Picture: fire spreading along fuses of different lengths from src.
   Which node catches fire next, and why can't anything reach it sooner?
2. "Lazy deletion": a node can sit in the heap several times. What do you
   do with an entry whose distance is no longer the node's best?
3. Why is "stop when dst is first discovered" wrong, and "stop when dst is
   popped" right?
4. What breaks if one edge is negative? What do you use instead?

Run:  pytest -k dijkstra
"""


def dijkstra(n: int, edges: list[tuple[int, int, float]], src: int) -> list[float]:
    raise NotImplementedError


def shortest_route(n: int, edges: list[tuple[int, int, float]], src: int, dst: int):
    raise NotImplementedError
