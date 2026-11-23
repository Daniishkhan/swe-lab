"""
Thread-safe LRU cache with single-flight (cache stampede coalescing)
Topic: 03.07  |  Priority: P0

A signature senior concurrency problem (Anthropic & Google): when 100 threads
miss the same cold key at once, only ONE thread should call the expensive
downstream loader while the other 99 wait for its result—WITHOUT blocking
requests for other keys.

API
---
class SingleFlightCache:
    __init__(self, capacity: int)
        capacity < 1 raises ValueError.

    get_or_load(self, key, loader) -> Any
        - If `key` is cached, mark it most-recently-used and return its value
          (including falsy values like None, 0, False, "").
        - If `key` is already being loaded by another thread, wait for that
          in-flight load to finish and return its value (or re-raise its
          exception if it failed). Do NOT call `loader` a second time.
        - Otherwise, register an in-flight entry for `key`, release the cache
          lock, invoke `loader()`, store the result (evicting the least
          recently used entry if over capacity), notify all waiters, and return.
        - If `loader()` raises an exception, do NOT cache the failure; clear
          the in-flight entry and wake all waiters so they observe the error
          and a subsequent call can retry.

    __len__(self) -> int
        Number of currently cached entries (thread-safe).

What the tests measure
----------------------
- Stampede coalescing: 30 threads requesting the same cold key invoke loader
  EXACTLY once.
- No global lock during I/O: a slow load for key "a" must NOT block concurrent
  loads for key "b" or hits on key "c".
- Failure recovery: if loader fails, waiters see the error, nothing is cached,
  and the next call retries cleanly.
- LRU eviction: capacity is enforced under sequential and concurrent access.

Before you code (say it out loud)
---------------------------------
1. Why is holding the cache lock while calling `loader()` catastrophic?
2. What happens if `loader()` raises an exception and you forget to signal
   the waiter Event / clean up the in-flight map in a `finally` block?
3. Why must you check `key in cache` (not `cache.get(key)`) for falsy values?

Run:  python3 -m pytest -k single_flight_cache
"""


class SingleFlightCache:
    def __init__(self, capacity):
        raise NotImplementedError

    def get_or_load(self, key, loader):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError
