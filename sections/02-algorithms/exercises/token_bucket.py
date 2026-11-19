"""
Token bucket rate limiter (single process)
Topic: 02.14  |  Priority: P2

Problem
-------
A bucket holds up to `capacity` tokens and refills continuously at
`refill_per_sec`. Each request spends `cost` tokens; if there are not enough,
it is rejected.

Requirements
------------
- The bucket starts full.
- allow(cost=1) -> True and spends tokens, or False and spends nothing.
- Refill is lazy: compute it from elapsed time on each call, no timer thread.
- Never exceed capacity.
- `clock` is injectable so tests can control time. Default: time.monotonic.

Before you code (say it out loud)
---------------------------------
1. Physical picture: a bucket with a dripping tap. What does capacity control
   (burst) vs refill rate (sustained rate)?
2. Why time.monotonic and not time.time?
3. Compare with leaky bucket and sliding window counter. When pick each?

Follow-up: make it thread-safe (section 03), then distributed (section 07).

Run:  pytest -k token_bucket
"""

import time
from typing import Callable


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float,
                 clock: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def allow(self, cost: float = 1) -> bool:
        raise NotImplementedError
