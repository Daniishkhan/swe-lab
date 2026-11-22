"""
Hash map from scratch (separate chaining)
Topic: 01.01  |  Priority: P0

Problem
-------
Build a hash map without using dict or set internally: sections 4 to 7 of the
chapter. Keep a list of buckets. Each bucket is a list of (key, value) pairs
whose keys landed in that bucket (slot = hash(key) % capacity).

    m = HashMap()
    m.put("cat", 1); m.put("tac", 2)   # may share a bucket; both are kept
    m.get("tac")  -> 2
    len(m)        -> 2

Requirements
------------
- put(key, value): insert, or overwrite the value if the key is already there.
- get(key): return the value; raise KeyError if missing.
- remove(key): delete; raise KeyError if missing.
- `key in m` and len(m) work. None is a valid value.
- Grow when len / capacity would exceed max_load_factor, by a multiple
  (doubling is the usual choice; x1.5 also passes), and rehash every key
  into the new buckets.
- `capacity` reports the current number of buckets.
- bucket_sizes() returns a list with the length of every bucket's chain
  (len(m.bucket_sizes()) == m.capacity). The tests read it.
- Target: O(1) average for put / get / remove, amortized over resizes.

What the tests measure
----------------------
They use keys that count every == and every hash() call. Looking up 5,000
keys must average only a few == each, the longest chain must stay short,
and the capacity must grow by a multiple (a handful of resizes), not by a
fixed step.

Before you code (say it out loud)
---------------------------------
1. Why must each bucket store the key, not just the value?
2. What does the load factor have to do with speed? What happens at load 5?
3. What does a resize cost, and why is it still O(1) amortized?
4. Why can't a resize copy bucket i to bucket i?

Run:  pytest -k test_hash_map
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

    def bucket_sizes(self) -> list[int]:
        raise NotImplementedError
