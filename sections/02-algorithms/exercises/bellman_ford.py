"""
Bellman-Ford: shortest paths with negative edges, and negative cycles
Topic: 02.08  |  Priority: P1

Problem
-------
A directed graph with nodes 0..n-1 and edges (u, v, w). Weights can be
negative: a refund, a downhill stretch that charges a battery, a currency
trade. Parallel edges and self-loops can appear.

    edges = [(0, 1, 2), (0, 2, 5), (2, 1, -4)]
    bellman_ford(3, edges, 0)     ->  [0, 1, 5]     (Dijkstra would say dist[1] = 2)

    edges = [(0, 1, 1), (1, 2, 1), (2, 1, -3)]
    bellman_ford(3, edges, 0)     ->  None          (1 -> 2 -> 1 costs -2 per lap)
    negative_cycle(3, edges)      ->  [1, 2] or [2, 1]

Functions
---------
bellman_ford(n, edges, src) -> list | None
    dist[i] = the least total weight of a path from src to i (math.inf if
    unreachable), or None if a negative cycle can be reached from src
    (then "least" doesn't exist). A negative cycle src can't reach doesn't
    matter: return the distances.
    Target: O(V * E) time in the worst case, O(V) extra space. Stop early:
    as soon as a full round over the edges changes nothing, you are done.

negative_cycle(n, edges) -> list | None
    Any one cycle whose total weight is negative, anywhere in the graph (not
    only the part node 0 can reach), as its nodes in order:
    [c0, c1, ..., ck] with edges c0 -> c1 -> ... -> ck -> c0. None if the
    graph has no negative cycle. A negative self-loop is the cycle [v].
    Target: O(V * E) time, O(V) extra space. One run, not one per node.

How the tests measure your work
-------------------------------
Every weight is a float subclass that counts how often it is added to
something. Use the weights as they come (no float(w) or int(w) copies).
- A graph whose shortest paths are all at most 5 edges long gives you a
  budget of about 8 rounds over the edges, not V - 1 rounds: stop early.
- negative_cycle gets a budget of about V + 1 rounds, so running
  Bellman-Ford once from every node fails, in whatever order you try them.

Before you code (say it out loud)
---------------------------------
1. After round k, which distances are guaranteed right? So why V - 1 rounds?
2. Why does a V-th round that still improves something prove a negative
   cycle? Why can it be a node *behind* the cycle that improves?
3. How do you find a cycle that node 0 can't reach without one run per
   node? (Hint: what if every node started at distance 0?)
4. From a node that improved in round V, how do you walk to a node that is
   surely on the cycle?

Run:  pytest -k bellman_ford
"""


def bellman_ford(n: int, edges: list[tuple[int, int, float]], src: int) -> list[float] | None:
    raise NotImplementedError


def negative_cycle(n: int, edges: list[tuple[int, int, float]]) -> list[int] | None:
    raise NotImplementedError
