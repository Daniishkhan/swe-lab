"""
Binary search tree with delete, successor and range queries
Topic: 01.03  |  Priority: P0

Problem
-------
Build a plain (unbalanced) binary search tree: sections 3 to 6 of the
chapter. Each node holds a key and left / right pointers. Keys are unique.

    t = BST()
    for k in [50, 30, 70, 20, 40, 60, 80]:
        t.insert(k)
    t.successor(50)   -> 60
    t.range(25, 65)   -> [30, 40, 50, 60]
    t.delete(50)      # two children: the successor's key moves up
    list(t)           -> [20, 30, 40, 60, 70, 80]

Requirements
------------
- insert(key) -> bool: True if added, False if the key was already there.
- contains(key) -> bool, and `key in t`.
- delete(key): remove it, handling leaf, one-child and two-children nodes;
  raise KeyError if the key isn't there.
- min(), max(): the smallest / largest key; raise ValueError when empty.
- successor(key): the smallest key strictly greater than `key`, or None.
  `key` doesn't have to be in the tree.
- range(lo, hi): a sorted list of the keys k with lo <= k < hi.
- iter(t): the keys in sorted order. len(t): how many keys.
- height(): the number of levels (empty tree 0, one node 1).
- Keys only need <, >, == (they may not be numbers). No dict, set, sort or
  bisect inside: the tree itself must do the work.
- Target: O(height) for insert, contains, delete, min, max, successor;
  O(height + k) for a range returning k keys; O(n) to iterate.
- Don't balance it. Inserting 1, 2, ..., n in order must give height n.

What the tests measure
----------------------
They use keys that count every comparison. On a 16,383-key tree of height
14, a search, successor or delete may compare with only a few keys per
level, min and max with fewer than one per level, and a range query
returning k keys with about two boundary paths plus k. Walking the whole
tree for any of these fails.

Before you code (say it out loud)
---------------------------------
1. State the BST rule precisely. Why is "left child < node < right child"
   not enough?
2. In the two-children delete, why the successor, and why does its old node
   never have two children?
3. How does a successor search from the root know which node to remember?
4. Why does inserting sorted keys make every operation O(n)?

Run:  pytest -k bst
"""


class BST:
    def __init__(self):
        raise NotImplementedError

    def insert(self, key) -> bool:
        raise NotImplementedError

    def contains(self, key) -> bool:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        return self.contains(key)

    def delete(self, key) -> None:
        raise NotImplementedError

    def min(self):
        raise NotImplementedError

    def max(self):
        raise NotImplementedError

    def successor(self, key):
        raise NotImplementedError

    def range(self, lo, hi) -> list:
        raise NotImplementedError

    def height(self) -> int:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
