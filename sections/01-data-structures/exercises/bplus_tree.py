"""
B+tree on a page store
Topic: 01.13  |  Priority: P2

Problem
-------
Build sections 3 and 4 of the chapter: a B+tree whose nodes live in pages
on a simulated disk. To look at a node you must read its page, and to change
a node you must write the page back. The tests count those reads and writes,
the way a database counts disk I/Os.

    disk = Disk(max_keys=3)
    t = BPlusTree(disk)
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        t.put(k, str(k))
    t.get(6)                -> "6"
    t.get(99)               -> None
    list(t.range(6, 17))    -> [(6, "6"), (7, "7"), (10, "10"), (12, "12")]
    t.height()              -> 2

The page store (given: read it, use it, don't change it)
-------------------------------------------------------
- Node(leaf, keys, vals, next) is one page.
  A leaf: keys sorted, vals[i] is the value of keys[i], and next is the page
  id of the leaf to its right (None for the last leaf).
  An internal node: keys are separators and vals holds the child page ids,
  one more than there are keys. Child i holds every key k with
  keys[i - 1] <= k < keys[i] (bisect.bisect_right finds i).
- disk.alloc() returns a new page id. disk.read(pid) returns a COPY of the
  node, so changing it does nothing until you disk.write(pid, node) it back.
  disk.write raises PageFull if the node has more than disk.max_keys keys:
  split first, then write.

Requirements
------------
- BPlusTree(disk): an empty tree is one empty leaf, which is the root. Keep
  only the root's page id in memory (self.root); every node lives in a page.
- put(key, value): insert, or replace the value if the key is already there.
  A node that would get more than max_keys keys splits in half. A leaf split
  COPIES the right half's first key up into the parent; an internal split
  MOVES its middle key up. When the root splits, a new root is made above
  it: the tree grows at the top, so all leaves stay at the same depth.
- get(key, default=None): the value, or default.
- range(lo, hi): a generator of (key, value) pairs with lo <= key < hi, in
  key order. Find the first leaf once, then walk the leaf chain with next.
- height(): the number of levels (a tree that is one leaf has height 1).
- Keys only need < and ==. No deletes.

What the tests measure
----------------------
They count disk.reads and disk.writes:
- get reads one page per level: at most height() reads.
- put reads at most height() pages and writes only the pages it changes:
  20,000 random puts must cost under 1.5 writes each on average (with
  max_keys = 16, a split is rare, so most puts write one leaf). Writing
  every page on the path back "just in case" costs about 4 per put.
- range over about 1,000 keys reads the path down plus the leaves it covers
  (about 1,000 / 8 at most), not every leaf from the left edge.
- range is lazy: taking its first 5 items reads at most height() + 1 pages.
- The shape: every leaf at the same depth, keys sorted, separators correct,
  the leaf chain visits every key in order, every node except the root at
  least half full (max_keys // 2 keys), and height() within the B-tree bound.

Before you code (say it out loud)
---------------------------------
1. Why is a leaf split a copy up, but an internal split a move up?
2. Why does the tree grow at the root and never at the leaves?
3. With max_keys = 16, how many levels does 1,000,000 keys need, at most?
4. What breaks in range() if a leaf split forgets to fix the next pointer?

Run:  pytest -k bplus_tree
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# The page store. Given: don't change it.
# ---------------------------------------------------------------------------
class PageFull(Exception):
    """A node has more keys than a page can hold."""


@dataclass
class Node:
    leaf: bool
    keys: list = field(default_factory=list)
    vals: list = field(default_factory=list)  # leaf: values; internal: child page ids
    next: int | None = None                    # leaf only: the page id of the next leaf


def _copy(node: Node) -> Node:
    return Node(node.leaf, list(node.keys), list(node.vals), node.next)


class Disk:
    """Pages addressed by integer ids. Counts every read and write."""

    def __init__(self, max_keys: int = 4):
        if max_keys < 3:
            raise ValueError("max_keys must be at least 3")
        self.max_keys = max_keys
        self.pages: dict[int, Node | None] = {}
        self.reads = 0
        self.writes = 0

    def alloc(self) -> int:
        pid = len(self.pages)
        self.pages[pid] = None
        return pid

    def read(self, pid: int) -> Node:
        node = self.pages[pid]
        if node is None:
            raise ValueError(f"page {pid} was allocated but never written")
        self.reads += 1
        return _copy(node)

    def write(self, pid: int, node: Node) -> None:
        if pid not in self.pages:
            raise KeyError(f"page {pid} was never allocated")
        if len(node.keys) > self.max_keys:
            raise PageFull(f"page {pid}: {len(node.keys)} keys, but a page holds {self.max_keys}")
        want = len(node.keys) if node.leaf else len(node.keys) + 1
        if len(node.vals) != want:
            raise ValueError(f"page {pid}: {len(node.keys)} keys need {want} vals, got {len(node.vals)}")
        self.writes += 1
        self.pages[pid] = _copy(node)


# ---------------------------------------------------------------------------
# Your B+tree.
# ---------------------------------------------------------------------------
class BPlusTree:
    def __init__(self, disk: Disk):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def range(self, lo, hi):
        raise NotImplementedError

    def height(self) -> int:
        raise NotImplementedError
