"""
Skip list: a sorted set with express lanes
Topic: 01.11  |  Priority: P2

Problem
-------
Build sections 4 to 6 and 8 of the chapter: a sorted set stored as a skip
list. Level 0 is a sorted singly linked list of every key. Each level above
it is an express lane: a sorted linked list of some of the keys of the level
below. A new key's height comes from coin flips and never changes.

    s = SkipList(rng=random.Random(1))
    for x in [30, 10, 50, 20, 40]:
        s.insert(x)                 # True each time
    s.insert(20)       -> False     (already there; nothing changes)
    20 in s            -> True
    list(s)            -> [10, 20, 30, 40, 50]
    s.range_query(15, 40) -> [20, 30, 40]
    s.remove(30)       -> True
    s.remove(30)       -> False
    len(s)             -> 4
    s.level_keys(0)    -> [10, 20, 40, 50]

Requirements
------------
- SkipList(p=0.5, max_level=32, rng=None). rng is a random.Random; if it's
  None, make your own random.Random(). Take every coin flip from it, so a
  seeded run is repeatable. A node's height is 1 plus the number of heads
  (each with probability p) before the first tails, capped at max_level.
  A node of height h sits on levels 0 .. h - 1.
- insert(key) -> bool: add key, True if it was new, False if it was already
  there. Expected O(log n).
- remove(key) -> bool: True if it was there. Expected O(log n).
- key in s: expected O(log n). len(s): O(1).
- iter(s): every key, ascending, O(n): walk level 0.
- range_query(lo, hi) -> list: the keys with lo <= key <= hi, ascending.
  Expected O(log n + k) for k results: find lo, then walk level 0.
  lo > hi gives [].
- level_keys(i) -> list: the keys on level i (0 is the bottom), ascending.
  Above the top level, []. The tests use it to check the shape.
- Keys only need < and == (numbers, strings, tuples, or objects that aren't
  hashable). So don't keep a dict or set of the keys, and don't use
  float("inf") or other sentinel keys: use None for "no next node".
- No list.sort(), sorted(), bisect or a Python list of all the keys: the
  linked levels must do the work.

What the tests measure
----------------------
They use keys that count every comparison (<, <=, >, >=, ==, !=) and can't
be hashed:
- inserting 4,096 keys in random, rising or falling order must average at
  most 4 log2 n + 20 = 68 comparisons per insert (a skip list needs about
  20 to 25 at p = 1/2; a sorted linked list about n / 2 = 2,048 in random
  order; an unbalanced BST about n / 2 on rising keys);
- membership tests and removals have the same budget per call;
- 200 range queries of about 10 keys each must cost at most
  4 log2 n + 20 + 2k comparisons each, so a range that walks from the head
  (about n / 2 comparisons) fails;
- the shape: level 0 holds every key, each level is a subset of the one
  below, and level i holds about n * p^i keys (within 30%) for p = 1/2 and
  p = 1/4; the number of levels stays near log(n) base 1/p; max_level caps it;
- 200,000 random ints inserted and looked up within a 20 s cap (a pure
  Python skip list takes about a second; a sorted linked list never
  finishes).

Before you code (say it out loud)
---------------------------------
1. Why does the search remember the last node it stood on at each level?
   Which pointers does an insert of height h change?
2. Why does the height come from coin flips and not from the key's position?
3. What happens to the levels when the tallest node is removed?
4. Why is the expected search cost about 2 log2 n at p = 1/2, for any order
   of inserts?

Run:  pytest -k "skip_list and not rank"
"""

import random


class SkipList:
    def __init__(self, p: float = 0.5, max_level: int = 32, rng: random.Random | None = None):
        raise NotImplementedError

    def insert(self, key) -> bool:
        raise NotImplementedError

    def remove(self, key) -> bool:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def range_query(self, lo, hi) -> list:
        raise NotImplementedError

    def level_keys(self, i: int) -> list:
        raise NotImplementedError
