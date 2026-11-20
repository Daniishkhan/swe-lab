"""
Sliding window counter (many keys, one process)
Topic: 02.14  |  Priority: P2

Problem
-------
Approximate "at most `limit` requests per key in any `window` seconds" with
two counts per key instead of a log of timestamps.

Time is cut into fixed windows aligned to multiples of `window`: window
number floor(now / window). Each key remembers how many requests it was
allowed in the current window and in the previous one. To judge a request,
assume the previous window's requests were spread evenly, and count only the
part of it that still overlaps the last `window` seconds:

    elapsed  = now - (current window number) * window
    estimate = previous * (window - elapsed) / window + current

A request is allowed if, counting it, the estimate stays at or under the
limit: estimate + 1 <= limit. Only allowed requests are counted.

    limit 100, window 60. 80 requests allowed in [0, 60).
    t=75: 30 more allowed so far in [60, 120).
    estimate("u") -> 80 * 45/60 + 30 = 90.0
    allow("u") -> True ... ten times (estimate 90 -> 100), then False.

Requirements
------------
- SlidingWindowCounter(limit, window, clock=time.monotonic). limit < 1 or
  window <= 0 raises ValueError.
- allow(key) -> bool, as above.
- estimate(key) -> float: the estimate right now, not counting a new
  request. Changes nothing. 0.0 for a key never seen.
- When the clock moves into the next window, the current count becomes the
  previous one. If it skips a whole window or more, both start from 0.
- O(1) time per call and O(1) memory per key, whatever the limit: no
  timestamps, no lists that grow with requests.
- Read the clock at most once per call. No timers, threads or sleeping.

Target: O(1) per call, O(1) memory per key.

Before you code (say it out loud)
---------------------------------
1. Run the boundary burst by hand: limit 100, 100 requests at t=59, then
   100 more at t=60. How many of the second hundred pass? Compare with a
   plain fixed window.
2. When is the estimate too low, and when too high? Draw the previous
   window's requests bunched at its end, then at its start.
3. How many bytes per key, and what does that come to at 10 million keys?

Run:  python3 -m pytest -k rate_window_counter
"""

import time
from typing import Callable, Hashable


class SlidingWindowCounter:
    def __init__(self, limit: int, window: float,
                 clock: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def allow(self, key: Hashable) -> bool:
        raise NotImplementedError

    def estimate(self, key: Hashable) -> float:
        raise NotImplementedError
