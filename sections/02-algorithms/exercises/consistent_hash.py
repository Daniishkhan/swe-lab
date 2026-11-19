"""
Consistent hashing ring with virtual nodes
Topic: 02.15  |  Priority: P2

Problem
-------
Map keys to nodes so that adding or removing a node moves only the keys that
have to move.

Requirements
------------
- ConsistentHashRing(vnodes=100): each physical node gets `vnodes` points on
  the ring.
- add_node(name), remove_node(name).
- get_node(key) -> name of the owning node (first ring point clockwise from
  hash(key)). Raise LookupError if the ring is empty.
- Must be deterministic across runs: do NOT use Python's built-in hash() for
  strings (it is randomized per process). Use hashlib (md5/sha1) instead.
- get_node in O(log N) using a sorted list + bisect.

Before you code (say it out loud)
---------------------------------
1. With plain `hash(key) % N`, what fraction of keys move when N changes?
2. Why do virtual nodes even out the load?
3. Compare with rendezvous (highest random weight) hashing.

Run:  pytest -k consistent_hash
"""


class ConsistentHashRing:
    def __init__(self, vnodes: int = 100):
        raise NotImplementedError

    def add_node(self, name: str) -> None:
        raise NotImplementedError

    def remove_node(self, name: str) -> None:
        raise NotImplementedError

    def get_node(self, key: str) -> str:
        raise NotImplementedError
