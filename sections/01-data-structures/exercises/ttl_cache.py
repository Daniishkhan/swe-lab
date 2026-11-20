"""
LRU cache with expiry (TTL)
Topic: 01.08  |  Priority: P1

Problem
-------
Section 11 of the chapter. An LRU cache where every entry also expires
`ttl` seconds after it was last written. Every entry gets the same ttl.
Time comes from the `clock` you are given (a function returning the current
time), so the tests can move time forward without sleeping.

    now = [0.0]
    c = TTLCache(capacity=2, ttl=10, clock=lambda: now[0])
    c.put("a", 1)            a expires at 10
    now[0] = 6
    c.put("b", 2)            b expires at 16
    c.get("a")    -> 1       (a is now the most recent; reading it does NOT
                              push its expiry back)
    now[0] = 10
    c.get("a")    -> None    (expired at 10: removed)
    len(c)        -> 1

Requirements
------------
- TTLCache(capacity, ttl, clock=time.monotonic): capacity an int >= 1 and
  ttl > 0, else ValueError.
- An entry written at time t expires at t + ttl: from then on (clock() >=
  t + ttl) it behaves as if it were never there.
- get(key, default=None): a live entry returns its value and becomes the
  most recently used. Reading does not change its expiry. An expired or
  missing key returns default.
- put(key, value): insert or overwrite. Either way the expiry restarts at
  clock() + ttl and the key becomes the most recently used. If the cache
  then holds more live entries than capacity, evict the least recently used
  live entry. Expired entries never cost a live entry its place.
- purge_expired(): remove every expired entry and return how many it
  removed.
- len(cache): the number of live entries. key in cache: is it live? Neither
  changes the recency order.
- get, put, in: O(1). len and purge_expired: O(1 + number of entries that
  expired since the last purge), amortized.

What the tests measure
----------------------
- The test clock returns times that count every comparison made with them
  (expires <= now and so on). With 20,000 live entries and 5 expired ones,
  purge_expired() and len() get 60 comparisons. Checking every entry's
  expiry costs 20,000.
- One test fills the cache, lets the oldest entries expire, then reads them
  in a different order than they were written, so the recency order and the
  expiry order differ. Purging must still be cheap.
- A randomized check against a slow, simple model you can check by reading it.

Hint: because every entry gets the same ttl, the order in which entries
expire is the order in which they were last written. That order is a
second list.

Before you code (say it out loud)
---------------------------------
1. Why is the least recently USED entry not always the next one to EXPIRE?
   Give a three-step example.
2. With one ttl for everyone, which entry expires next? With a different ttl
   per entry, what would you need instead?
3. When the cache is full and some entries have expired, which one should
   a put remove first, and why?
4. Expired entries that nobody reads still take memory. Who removes them?

Run:  pytest -k ttl_cache
"""

import time


class TTLCache:
    def __init__(self, capacity: int, ttl: float, clock=time.monotonic):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def purge_expired(self) -> int:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
