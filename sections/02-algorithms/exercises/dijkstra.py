"""
Dijkstra's shortest paths
Topic: 02.08  |  Priority: P1

Problem
-------
Directed graph, nodes 0..n-1, edges (u, v, w) with w >= 0.
Return a list `dist` where dist[i] is the shortest distance from src to i,
or math.inf if i is unreachable.

Requirements
------------
- O((V + E) log V) with a binary heap (heapq is fine).

Before you code (say it out loud)
---------------------------------
1. Physical picture: water flooding outward from src through pipes of
   different lengths. Which node gets wet next?
2. Why does a negative edge break this? What do you use instead?
3. "Lazy deletion": what do you do with stale heap entries?

Run:  pytest -k dijkstra
"""


def dijkstra(n: int, edges: list[tuple[int, int, float]], src: int) -> list[float]:
    raise NotImplementedError
