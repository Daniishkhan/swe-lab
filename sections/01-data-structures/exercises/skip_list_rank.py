"""
A mini Redis sorted set: skip list with spans, plus a dict
Topic: 01.11  |  Priority: P2

Problem
-------
Build sections 8 and 9 of the chapter: the structure behind Redis's ZADD,
ZSCORE, ZRANK and ZRANGE. Each member (a string) has a score (a number).
Members are kept in order of (score, member): lower score first, and equal
scores in alphabetical order of member, as Redis does.

    z = SortedSet(rng=random.Random(1))
    z.add("ann", 30)   -> True        (new member)
    z.add("bob", 10); z.add("cat", 20); z.add("dan", 20)
    z.rank("bob")      -> 0           (counts from 0, like ZRANK)
    z.rank("cat")      -> 1,  z.rank("dan") -> 2,  z.rank("ann") -> 3
    z.by_rank(0)       -> ("bob", 10)
    z.range_by_rank(1, 2) -> [("cat", 20), ("dan", 20)]   (both ends included)
    z.add("bob", 40)   -> False       (bob existed: his score is updated)
    z.rank("bob")      -> 3,  z.score("bob") -> 40
    z.remove("cat")    -> True,  z.rank("dan") -> 0
    z.rank("zed")      -> None,  z.score("zed") -> None,  len(z) -> 3

Requirements
------------
- SortedSet(p=0.25, max_level=32, rng=None): a skip list ordered by
  (score, member), plus a dict from member to score. Take every coin flip
  from rng (a random.Random; make your own if it's None).
- add(member, score) -> bool: True if the member is new. If it exists with
  a different score, move it (remove, then insert). Expected O(log n).
- remove(member) -> bool. Expected O(log n).
- score(member): the score, or None. O(1): it must not search the skip list.
- rank(member): its 0-based position, or None. Expected O(log n): add up
  the spans of the links you follow (section 8). Never walk level 0 to count.
- by_rank(r) -> (member, score) for 0 <= r < len, else IndexError.
  Expected O(log n), again with spans.
- range_by_rank(start, stop) -> list of (member, score) for ranks start..stop
  inclusive (like ZRANGE), with start >= 0 and stop clipped to len - 1.
  start > stop, or start >= len, gives []. Expected O(log n + m).
- len(z): O(1).
- Each link stores its span: how many level-0 steps it covers. Keep spans
  right on every insert and remove (the chapter's section 8 has the rules).
- Scores only need < and ==. No sorting, no bisect, no Python list of all
  members kept in order.

What the tests measure
----------------------
- A random mix of 3,000 adds, updates and removes with many tied scores,
  checked against a brute-force sorted list after every step: wrong spans
  show up here first.
- score(): scores that count their comparisons; 2,000 score() calls must
  make zero comparisons (a dict lookup), so searching the skip list fails.
- rank(): 2,000 ranks in a set of 4,096 must average at most
  8 log2 n + 40 = 136 score comparisons each (a tuple comparison can cost
  two; a skip list needs about 25 to 50; walking level 0 and comparing
  scores about 4,000).
- by_rank(), range_by_rank() and rank(): 50,000 lookups by rank, 2,000
  ranges and 20,000 rank() calls in a set of 50,000 members, under a 15 s
  cap. With spans this takes about a second; walking level 0 to the r-th
  node (or to the member, counting) is over a billion steps.

Before you code (say it out loud)
---------------------------------
1. What does a span count? Why do the spans you follow add up to a rank?
2. When you insert a node of height h, what happens to the spans of the
   links at levels below h, and to the links at levels h and above that
   jump over the new node?
3. Why does Redis keep a dict next to the skip list? Which commands use
   which part?
4. Why order by (score, member) instead of score alone?

Run:  pytest -k skip_list_rank
"""

import random


class SortedSet:
    def __init__(self, p: float = 0.25, max_level: int = 32, rng: random.Random | None = None):
        raise NotImplementedError

    def add(self, member: str, score) -> bool:
        raise NotImplementedError

    def remove(self, member: str) -> bool:
        raise NotImplementedError

    def score(self, member: str):
        raise NotImplementedError

    def rank(self, member: str):
        raise NotImplementedError

    def by_rank(self, r: int) -> tuple:
        raise NotImplementedError

    def range_by_rank(self, start: int, stop: int) -> list:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
