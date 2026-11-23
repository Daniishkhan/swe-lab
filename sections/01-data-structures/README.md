# §01 Data Structures

Open `index.html` in this folder for the interactive chapter view (status tracking, links to concept pages and exercises).

## Topics

- [ ] `01.01` **[P0]** Arrays, strings, hash maps/sets: collision handling, load factor, resizing cost
- [ ] `01.02` **[P0]** Linked lists, stacks, queues, deques, monotonic stack/queue
- [ ] `01.03` **[P0]** Trees: BST, balanced trees (red-black, AVL at a conceptual level), traversal orders
- [ ] `01.04` **[P0]** Heaps and priority queues: top-k, k-way merge, scheduling
- [ ] `01.05` **[P0]** Graphs: adjacency list vs matrix, directed/undirected, weighted
- [ ] `01.06` **[P0]** Tries, prefix/radix trees (autocomplete, routing tables)
- [ ] `01.07` **[P0]** Union-find (disjoint sets) with path compression
- [ ] `01.08` **[P1]** LRU/LFU cache construction (hash map + doubly linked list)
- [ ] `01.09` **[P0]** Interval structures: merge, sweep line, interval tree basics
- [ ] `01.10` **[P1]** Segment trees, Fenwick trees (BIT)
- [ ] `01.11` **[P2]** Skip lists (and why Redis uses them)
- [ ] `01.12` **[P1]** Probabilistic structures: Bloom filter, Count-Min Sketch, HyperLogLog
- [ ] `01.13` **[P1]** Storage structures: B-tree, B+tree, LSM tree, SSTable, write-ahead log
- [ ] `01.14` **[P2]** Concurrent structures: lock-free queue, ring buffer, concurrent hash map

## Layout

```
01-data-structures/
├── index.html     chapter page (rendered from assets/curriculum.js)
├── concepts/      one HTML page per concept (python tools/new.py concept <topic-id> <slug> "Title")
├── exercises/     Python stubs + pytest tests; you write the solutions
└── notes.md       your own scratch notes
```
