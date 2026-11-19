"""
Graph basics: transpose, find the judge, pack into CSR
Topic: 01.05  |  Priority: P0

Problem
-------
Vertices are the numbers 0..n-1. A directed graph is an adjacency list:
adj[u] is the list of vertices u has an edge to.

1. transpose(adj): the same graph with every edge reversed, as a new
   adjacency list. Inside each new list, vertices appear in increasing order
   of where the edge came from (u = 0 first). Don't change adj.

       transpose([[1, 2], [2], []])  ->  [[], [0], [0, 1]]

2. find_judge(n, trust): n people, numbered 0..n-1. trust is a sequence of
   pairs (a, b) meaning "a trusts b"; no pair appears twice and nobody
   trusts themselves. The judge is the one person who trusts nobody and is
   trusted by all n - 1 others. Return the judge's number, or -1 if there is
   no judge.

       find_judge(3, [(0, 2), (1, 2)])  ->  2
       find_judge(3, [(0, 2), (1, 2), (2, 0)])  ->  -1
       find_judge(1, [])  ->  0

3. to_csr(adj): pack the adjacency list into two flat lists (the CSR layout
   from the chapter's section 9 aside). targets holds every list back to
   back; offsets has n + 1 entries, so u's neighbors are
   targets[offsets[u]:offsets[u + 1]]. Return (offsets, targets).

       to_csr([[1, 2], [2], []])  ->  ([0, 2, 3, 3], [1, 2, 2])

Requirements
------------
- All three in O(V + E) time: one pass over the edges, plus one over the
  vertices. Never build a V x V matrix: at 200,000 vertices that's
  40 billion cells.
- find_judge makes at most two passes over trust (one is enough); it
  doesn't need a set or a dict.

What the tests measure
----------------------
- find_judge gets a trust sequence that counts reads and gives up past
  2 reads per pair. Checking each candidate against every pair is
  O(V * E) reads.
- 200,000 vertices and 1,000,000 edges under a 5 s cap. Scanning every
  edge once per vertex, or growing a list with `targets = targets + lst`
  (which copies everything so far, every time), takes minutes.

Before you code (say it out loud)
---------------------------------
1. transpose: you walk u's list and see v. Whose list does u go into?
2. find_judge: what two numbers per person decide it, and what must they be
   for the judge?
3. to_csr: how does offsets[u + 1] follow from offsets[u]?

Run:  pytest -k graph_basics
"""

from collections.abc import Sequence


def transpose(adj: list[list[int]]) -> list[list[int]]:
    raise NotImplementedError


def find_judge(n: int, trust: Sequence[tuple[int, int]]) -> int:
    raise NotImplementedError


def to_csr(adj: list[list[int]]) -> tuple[list[int], list[int]]:
    raise NotImplementedError
