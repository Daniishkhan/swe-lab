# §02 Algorithms

> Google L5 bar: clarify ambiguity first, state brute force and complexity, optimize, write clean bug-resistant code in a bare editor without executing, hand-trace edge cases, and expect 2 to 3 escalating follow-ups.

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `02.01` **[P0]** Complexity analysis: time, space, amortized; knowing when constants matter
- [ ] `02.02` **[P0]** Sorting and its trade-offs (quicksort, mergesort, heapsort, counting/radix); stability
- [ ] `02.03` **[P0]** Binary search, including "search on the answer" variants
- [ ] `02.04` **[P0]** Two pointers, sliding window, prefix sums
- [ ] `02.05` **[P0]** BFS/DFS, topological sort, cycle detection, connected components
- [ ] `02.06` **[P0]** Recursion and backtracking (permutations, subsets, constraint search)
- [ ] `02.07` **[P0]** Dynamic programming: 1D/2D, knapsack family, LIS, edit distance, interval and DAG DP
- [ ] `02.08` **[P0]** Shortest paths: Dijkstra, 0-1 BFS, Bellman-Ford, A* basics
- [ ] `02.09` **[P1]** Minimum spanning tree (Kruskal, Prim)
- [ ] `02.10` **[P1]** Greedy algorithms and how to argue correctness
- [ ] `02.11` **[P1]** Bit manipulation
- [ ] `02.12` **[P1]** String algorithms: rolling hash, KMP at a conceptual level
- [ ] `02.13` **[P1]** Streaming and external algorithms: reservoir sampling, external merge sort, heavy hitters
- [ ] `02.14` **[P1]** Rate limiting algorithms: token bucket, leaky bucket, sliding window log/counter
- [ ] `02.15` **[P1]** Consistent hashing, rendezvous hashing
- [ ] `02.16` **[P1]** Basic probability and estimation for capacity reasoning

## Layout

```
02-algorithms/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
├── exercises/     Python stubs + pytest tests; you write the solutions
└── notes.md       your own scratch notes
```
