"""
Hash map with open addressing (linear probing and tombstones)
Topic: 01.01  |  Priority: P0

Problem
-------
Build section 8 of the chapter: a hash map that keeps one key per slot in a
single flat list. No dict or set inside. A key starts at slot
hash(key) % capacity; if that slot holds another key, try the next slot
(wrapping around at the end) until you find it or reach an empty slot.

    m = ProbingMap()
    m.put("cat", 1); m.put("tac", 2)   # if they share a home slot, tac moves on
    m.remove("cat")                     # leaves a tombstone, not an empty slot
    m.get("tac") -> 2                   # the tombstone keeps the search going

Requirements
------------
- put / get / remove / `in` / len, with the same behavior as HashMap
  (overwrite on put, KeyError on a missing get or remove, None is a value).
- remove leaves a tombstone. Searches walk past tombstones; an empty slot
  ends a search. put may reuse a tombstone's slot.
- Tombstones count toward how full the table is. When
  (live keys + tombstones) / capacity would exceed max_load_factor, rebuild:
  re-insert only the live keys, into a table sized for the LIVE keys (double
  only if they need it). A table full of tombstones gets cleaned, not doubled.
- `capacity` is the current number of slots.
- `probes`: add 1 every time you look at a slot, in every operation
  (including re-inserts during a rebuild). The tests read it.
- Target: O(1) average per operation, amortized over rebuilds.

What the tests measure
----------------------
Deletes must not hide keys further along a probe walk. 10,000 rounds of
insert-then-delete must not grow the table or slow lookups down. Lookups of
5,000 keys must average only a few probes. If a test fails with "took too
long", some search never meets an empty slot.

Before you code (say it out loud)
---------------------------------
1. Why does an empty slot let a search stop early?
2. Why does deleting by emptying a slot lose keys? Give a 3-key example.
3. Why must tombstones count toward the load, and why size the rebuild
   from the live keys only?
4. Why do open-addressing tables grow at a lower load factor than chaining?

Run:  pytest -k probing_map
"""


class ProbingMap:
    def __init__(self, initial_capacity: int = 8, max_load_factor: float = 0.5):
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
