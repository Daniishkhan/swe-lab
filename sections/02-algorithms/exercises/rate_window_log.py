"""
Sliding window log (many keys, one process)
Topic: 02.14  |  Priority: P2

Problem
-------
Allow at most `limit` requests per key in any `window` seconds, exactly.
Keep the time of every accepted request. A request accepted at time t
counts while now - t < window, so it stops counting at exactly t + window.
Rejected requests are not logged (section 3 of the chapter says why).

    log = SlidingWindowLog(limit=3, window=10, clock=clock)
    t=0  allow("ana") -> True       log: [0]
    t=4  allow("ana") -> True       log: [0, 4]
    t=5  allow("ana") -> True       log: [0, 4, 5]
    t=9  allow("ana") -> False      still 3 in (-1, 9]
    t=9  retry_after("ana") -> 1.0  the 0 leaves at 10
    t=10 allow("ana") -> True       0 left; log: [4, 5, 10]
    t=10 allow("bob") -> True       every key has its own log

Requirements
------------
- SlidingWindowLog(limit, window, clock=time.monotonic). limit < 1 or
  window <= 0 raises ValueError.
- allow(key) -> bool. Logs the request only if it is accepted.
- count(key) -> int: accepted requests from key still inside the window.
- retry_after(key) -> float: 0.0 if allow(key) would succeed now, else the
  seconds until the oldest logged request leaves the window.
- forget_idle() -> int: delete every key with nothing left in its window
  and return how many were deleted. Their memory must really be freed.
- Old timestamps must be thrown away, not just skipped: one busy key holds
  at most `limit` timestamps, however long it runs.
- Amortized O(1) per call for any limit: no scan or copy of the whole log on
  every request. (Each timestamp goes in once and comes out once.)
- Read the clock at most once per call. No timers, threads or sleeping.

Target: amortized O(1) per call; memory O(limit) per active key.

Before you code (say it out loud)
---------------------------------
1. Why is this exact, when the fixed window counter lets 2x through at a
   window boundary?
2. Price the memory: 10 million keys, limit 1,000 per hour, 8 bytes per
   timestamp (and Python's real cost per float in a deque).
3. What would logging rejected requests do to a client that keeps
   retrying at twice the limit?

Run:  python3 -m pytest -k rate_window_log
"""

import time
from typing import Callable, Hashable


class SlidingWindowLog:
    def __init__(self, limit: int, window: float,
                 clock: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def allow(self, key: Hashable) -> bool:
        raise NotImplementedError

    def count(self, key: Hashable) -> int:
        raise NotImplementedError

    def retry_after(self, key: Hashable) -> float:
        raise NotImplementedError

    def forget_idle(self) -> int:
        raise NotImplementedError
