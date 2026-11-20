"""
LFU cache in O(1): a list of keys per use count
Topic: 01.08  |  Priority: P1

Problem
-------
Sections 8 and 9 of the chapter. A cache of at most `capacity` entries that,
when full, throws out the key used the FEWEST times. Among keys tied on
the fewest uses, it throws out the least recently used one.

    c = LFUCache(2)
    c.put("a", 1)          a: 1 use
    c.put("b", 2)          b: 1 use
    c.get("a")   -> 1      a: 2 uses
    c.put("c", 3)          full: b has the fewest uses (1), so b goes
    c.get("b")   -> None
    c.get("c")   -> 3      c: 2 uses, tied with a; a is now the least recent
    c.put("d", 4)          full: a and c tie at 2 uses; a is less recent, so a goes
    c.frequency("c") -> 2

Requirements
------------
- LFUCache(capacity): capacity must be an int >= 1, else raise ValueError.
- get(key, default=None): a hit returns the value and adds one use.
  A miss returns default and changes nothing.
- put(key, value): an existing key gets the new value and one more use
  (it never evicts). A new key starts with 1 use; if the cache is full,
  evict first: fewest uses, ties broken by least recently used.
- frequency(key): the key's use count, or 0 if it isn't cached. It does not
  count as a use. An evicted key that comes back starts again at 1.
- key in cache (__contains__) and len(cache) don't count as uses.
- get, put, frequency, in and len: O(1). No heapq, no sorting, no scanning.

What the tests measure
----------------------
- Keys that count every __hash__ and __eq__ call: the budget is 10 per
  operation over 20,000 mixed operations. Scanning a list of keys, or
  min(self.counts, key=self.counts.get) to find the victim, fails.
- 300,000 operations with capacity 50,000 under a 10 s cap (well under a
  second with frequency buckets). Scanning every entry for the victim on
  each eviction costs about 50,000 steps per eviction and takes minutes.
- A randomized check against a slow, simple model you can check by reading it, which
  catches ties broken by insertion order instead of recency.
- A heap of (count, time, key) with lazy deletion is O(log n), not O(1).
  The tests can't tell it apart, but the interviewer asking for O(1) can.

Before you code (say it out loud)
---------------------------------
1. What are the buckets, and why is each one a doubly linked list rather
   than a set?
2. How do you know the smallest use count without searching? When can it
   change, and by how much?
3. Why can a new key's arrival always reset that smallest count to 1?
4. Trace the example above, drawing the buckets after every line.

Run:  pytest -k lfu_cache
"""


class LFUCache:
    def __init__(self, capacity: int):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def frequency(self, key) -> int:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
