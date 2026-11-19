"""
Graph traversal: topological sort and connected components
Topic: 02.05  |  Priority: P0

Problem
-------
Nodes are 0..n-1.
1. topological_sort(n, edges): edges are directed (u, v) meaning "u before v".
   Return any valid ordering, or None if there is a cycle.
2. count_components(n, edges): edges are undirected. Return the number of
   connected components.

Requirements
------------
- Both O(V + E). Build an adjacency list first.
- Use BFS (Kahn's algorithm) or DFS with colors for (1); try both.
- Watch recursion depth in Python for DFS on large graphs.

Before you code (say it out loud)
---------------------------------
1. Adjacency list vs matrix: which here, and why?
2. Kahn's algorithm: what does in-degree 0 mean physically (no prerequisites)?
3. How does each approach detect a cycle?

Run:  pytest -k graphs
"""


def topological_sort(n: int, edges: list[tuple[int, int]]) -> list[int] | None:
    raise NotImplementedError


def count_components(n: int, edges: list[tuple[int, int]]) -> int:
    raise NotImplementedError
