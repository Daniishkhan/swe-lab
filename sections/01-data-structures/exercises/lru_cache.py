"""
LRU cache: a hash map plus a doubly linked list
Topic: 01.08  |  Priority: P1

Problem
-------
Sections 3 to 5 of the chapter. A cache that holds at most `capacity`
entries. When it is full and a new key arrives, it throws out the entry that
was used least recently.

    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")      -> 1      ("a" is now the most recent)
    c.put("c", 3)             (full: evicts "b", the least recent)
    c.get("b")      -> None
    c.keys()        -> ["a", "c"]   (least recent first)

Build the doubly linked list yourself: a dict from key to node, and nodes
with prev and next pointers (sentinels at both ends save you the edge
cases). No collections.OrderedDict and no functools.

Requirements
------------
- LRUCache(capacity): capacity must be an int >= 1, else raise ValueError.
- get(key, default=None): the value, and the key becomes the most recent.
  A missing key returns default and changes nothing.
- put(key, value): insert or update. Either way the key becomes the most
  recent. Updating an existing key never evicts anything. Inserting a new
  key into a full cache evicts the least recently used key first.
- peek(key, default=None): the value WITHOUT changing the order.
- delete(key): remove the key; return True if it was there, else False.
- key in cache (__contains__) does not change the order. len(cache).
- keys(): a list of the keys from least to most recently used. O(n).
- get, put, peek, delete, in and len: O(1).

What the tests measure
----------------------
- The keys in two tests count every call to __hash__ and __eq__. A dict
  lookup costs about one of each, so the budget is 8 per operation over
  20,000 mixed operations. Keeping the order in a Python list fails:
  list.remove(key) and list.index(key) call __eq__ on every key they pass.
- 300,000 operations with capacity 50,000 run under a 10 s cap (a linked
  list takes well under a second). Finding the victim by scanning every
  entry for the oldest timestamp costs about 50,000 steps per eviction and
  takes minutes.
- A 200,000-entry cache takes 800,000 more new keys, so 800,000 evictions,
  under the same cap. A plain dict that evicts with next(iter(d)) passes
  every other test and fails this one: on CPython, iteration has to step
  over every slot deleted since the dict last resized (section 6).
- A randomized check against a slow, simple model you can check by reading it.
- The test reads your source and fails if it imports OrderedDict or
  functools.

Before you code (say it out loud)
---------------------------------
1. What does the dict give you that the list can't, and the other way round?
2. Why doubly linked? Which operation needs the prev pointer?
3. When you evict the tail node, how do you delete its entry from the dict?
   (What must the node remember?)
4. Draw the list before and after get() on a key in the middle. Which
   pointers change, and how many writes is that?

Follow-ups to think about: LFU (lfu_cache.py), expiry (ttl_cache.py), and
what a second thread calling get() would break.

Run:  pytest -k lru_cache
"""


class LRUCache:
    def __init__(self, capacity: int):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def peek(self, key, default=None):
        raise NotImplementedError

    def delete(self, key) -> bool:
        raise NotImplementedError

    def keys(self) -> list:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
