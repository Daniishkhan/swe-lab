"""
Striped hash map: many locks instead of one
Topic: 01.14  |  Priority: P2

Problem
-------
Build section 9 of the chapter: a thread-safe map that splits its keys into
`num_stripes` stripes, each guarded by its own lock, so threads working on
different stripes never wait for each other.

    m = StripedHashMap(num_stripes=4)
    m.put("alice", 100)
    m.compute("alice", lambda old: old + 5)      -> 105
    m.compute("bob", lambda old: (old or 0) + 1) -> 1
    m.transfer("alice", "bob", 30)               # alice 75, bob 31
    m.get("alice") -> 75,  m.total() -> 106,  len(m) -> 2

Requirements
------------
- StripedHashMap(num_stripes=16, lock_factory=threading.Lock). Make the locks
  with one call of lock_factory() per stripe, in stripe order, and keep them
  in self.locks (stripe i is guarded by self.locks[i]). Use them with
  `with lock:` (or acquire/release).
- stripe_of(key) -> int: hash(key) % num_stripes.
- get(key, default=None), put(key, value), delete(key) -> bool (True if the
  key was there), compute(key, fn): each takes exactly one lock, the key's
  stripe lock, and holds it for the whole operation.
- compute(key, fn): call fn(current value, or None if the key is missing)
  exactly once, while holding the stripe lock, so "read, change, write" is
  one atomic step (section 2's lost update can't happen). Store and return
  what fn returns; if it returns None, remove the key. If fn raises, the
  map is unchanged and the lock is released.
- transfer(src, dst, amount): move `amount` from src's value to dst's
  (a missing key counts as 0; both keys hold their new values afterwards,
  even when one is 0). Raise ValueError, changing nothing, if amount < 0 or
  src holds less than amount. Hold both keys' stripe locks for the whole
  move, taking them in increasing stripe order (section 9: a fixed order
  means no deadlock). If both keys share a stripe, take that lock once:
  threading.Lock is not re-entrant, so taking it twice hangs forever.
- total() -> the sum of all values, as one consistent snapshot: take every
  stripe lock, in increasing order, hold them all while you add up, then
  release them. (This is the expensive "stop the world" operation.)
- len(m): the number of keys, from per-stripe counts, without taking any
  lock. Under concurrent writes it may be a moment out of date; say why
  that is acceptable.
- Each stripe can store its keys in a plain dict.

What the tests measure
----------------------
They hand you a lock_factory whose locks record every acquire and release:
- which locks each operation takes, and how many: get, put, delete and
  compute exactly one, the key's stripe; len none; transfer one or two in
  increasing order; total all of them, held at the same time;
- that 1,024 keys spread over all 16 stripes (one global lock for
  everything puts every operation on one lock);
- that fn in compute runs while its stripe lock is held, and that locks are
  released after errors;
- then real threads, with real locks: 8 threads doing 3,000 compute()
  increments each must lose no update, and 6 threads doing random transfers
  while another calls total() must never see money appear or vanish, and
  must not deadlock.

Before you code (say it out loud)
---------------------------------
1. With 16 threads and one lock, how many can be inside the map at once?
   With 16 stripes and random keys?
2. Why does transfer take the lower stripe first? Draw the deadlock you get
   if it locks src then dst.
3. Why can't you get a consistent total by locking one stripe at a time?
4. Which workload makes striping useless? (Hint: one very hot key.)

Run:  pytest -k striped_hash_map
"""

import threading


class StripedHashMap:
    def __init__(self, num_stripes: int = 16, lock_factory=threading.Lock):
        raise NotImplementedError

    def stripe_of(self, key) -> int:
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def delete(self, key) -> bool:
        raise NotImplementedError

    def compute(self, key, fn):
        raise NotImplementedError

    def transfer(self, src, dst, amount) -> None:
        raise NotImplementedError

    def total(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
