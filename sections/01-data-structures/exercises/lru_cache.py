"""
LRU cache
Topic: 01.08  |  Priority: P1  |  Pattern: hash map + doubly linked list

Problem
-------
A fixed-capacity cache that evicts the least recently used entry when full.
Build the doubly linked list yourself (no OrderedDict, no functools.lru_cache).

Requirements
------------
- LRUCache(capacity): capacity must be >= 1, otherwise raise ValueError.
- get(key, default=None): return value and mark key as most recently used.
- put(key, value): insert or update, mark as most recently used, evict the LRU
  entry if over capacity.
- len(cache) returns the number of entries.
- Target: O(1) for get and put.

Before you code (say it out loud)
---------------------------------
1. Why do you need both a hash map and a linked list? What does each give you?
2. Why doubly linked rather than singly linked?
3. How do sentinel (dummy) head/tail nodes remove edge cases?

Follow-up to think about: how would you make this LFU? Thread-safe? Add TTLs?

Run:  pytest -k lru_cache
"""


class LRUCache:
    def __init__(self, capacity: int):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
