"""
Union-find patterns: linked accounts, growing islands, minimum spanning tree
Topic: 01.07  |  Priority: P1

Problem
-------
Sections 8 and 9 of the chapter. You may import your UnionFind from
union_find, or write a small one in this file.

1. link_accounts(accounts): accounts[i] is a list of identifiers (emails,
   phone numbers, card fingerprints). Two accounts that share an identifier
   belong to the same person, and so does everything linked to them through
   a chain of shared identifiers. Return the groups of account indexes:
   each group sorted, and the groups sorted by their smallest index.

       link_accounts([["a", "b"], ["c"], ["b", "d"], [], ["d", "e"], ["c"]])
           -> [[0, 2, 4], [1, 5], [3]]

2. islands_after_each(rows, cols, cells): a rows x cols grid starts as all
   water. cells is a list of (r, c), each turned into land in that order
   (a cell may be listed twice; the second time changes nothing). Land cells
   that touch up, down, left or right are one island. Return the number of
   islands after each step.

       islands_after_each(3, 3, [(0, 0), (0, 1), (1, 2), (2, 1), (1, 1)])
           -> [1, 1, 2, 3, 1]

3. min_spanning_tree(n, edges): n places 0..n-1 and edges (u, v, w), meaning
   a cable between u and v costs w. Pick edges that connect every place for
   the lowest total cost. Return (total, chosen) where chosen lists the
   picked edges exactly as they appear in edges, or None if some places
   can't be connected at all. n = 0 or 1 needs no edges: (0, []).

       min_spanning_tree(4, [(0, 1, 1), (1, 2, 2), (0, 2, 3), (2, 3, 4), (1, 3, 5)])
           -> (7, [(0, 1, 1), (1, 2, 2), (2, 3, 4)])

   Several spanning trees can tie for the lowest total; any of them is fine.

Requirements
------------
- link_accounts: O(L alpha(N)) after hashing, for N accounts with L
  identifiers in total. Map each identifier to the first account that had
  it (a dict), and union instead of comparing accounts pairwise.
- islands_after_each: O(k alpha(rows * cols)) for k steps, plus O(rows * cols)
  to set up. Don't recount the whole grid after each step.
- min_spanning_tree: Kruskal's algorithm: O(E log E) for the sort, then
  O(E alpha(n)) for the unions.

What the tests measure
----------------------
Correctness against slow brute forces on small random inputs, then a time
cap on inputs where the slow way is hopeless:
- link_accounts: 100,000 accounts under a 10 s cap (well under a second
  with a dict and union-find). Comparing every pair of accounts is 5 * 10^9 set
  intersections.
- islands_after_each: 60,000 steps on a 300 x 300 grid under a 10 s cap
  (well under a second). Recounting with BFS after every step is over 10^9 cell visits.
- min_spanning_tree: 100,000 places and 300,000 edges under a 10 s cap
  (under a second, most of it sorting). Checking "already connected?" with a BFS, or relabelling a
  whole label list on every merge, is over 10^9 steps.

Before you code (say it out loud)
---------------------------------
1. link_accounts: what are the items in the union-find: accounts or
   identifiers? What does the dict remember, and why is one owner enough?
2. islands_after_each: why does each new land cell start by adding 1 island,
   and when does a union take one away again? What changes if the same cell
   comes twice?
3. min_spanning_tree: why sort by cost? What does union returning False tell
   you about the edge? When can you stop early?

Run:  pytest -k union_find_patterns
"""


def link_accounts(accounts: list[list[str]]) -> list[list[int]]:
    raise NotImplementedError


def islands_after_each(rows: int, cols: int, cells: list[tuple[int, int]]) -> list[int]:
    raise NotImplementedError


def min_spanning_tree(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[tuple[int, int, int]]] | None:
    raise NotImplementedError
