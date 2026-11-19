"""
Hash map from scratch (separate chaining)
Topic: 01.01  |  Priority: P0

Problem
-------
Build a hash map without using dict or set internally. Use a list of buckets,
where each bucket holds (key, value) pairs that hashed to the same slot.

Requirements
------------
- put(key, value): insert or overwrite.
- get(key): return the value, raise KeyError if missing.
- remove(key): delete, raise KeyError if missing.
- `key in m` and len(m) work.
- Grow (double) the bucket array when len / capacity would exceed max_load_factor.
- `capacity` reports the current number of buckets.
- Target: O(1) average for put/get/remove, amortized over resizes.

Before you code (say it out loud)
---------------------------------
1. Why does load factor drive performance? What happens at load factor 5?
2. What does a resize cost, and why is it still O(1) amortized?
3. What happens when two different keys have the same hash?

Run:  pytest -k hash_map
"""


class HashMap:
    def __init__(self, initial_capacity: int = 8, max_load_factor: float = 0.75):
        raise NotImplementedError

    @property
    def capacity(self) -> int:
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def remove(self, key) -> None:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
