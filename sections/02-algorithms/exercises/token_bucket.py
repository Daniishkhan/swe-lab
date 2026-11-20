"""
Token bucket (one key, one process)
Topic: 02.14  |  Priority: P2

Problem
-------
A jar holds up to `capacity` tokens. A tap adds `rate` tokens per second,
continuously (fractions too), and stops adding when the jar is full. Each
request takes `cost` tokens. If the jar holds fewer than `cost` tokens, the
request is rejected and takes nothing.

    b = TokenBucket(capacity=5, rate=2, clock=clock)   # jar starts full: 5
    5 x b.allow()   -> True                            # jar: 0
    b.allow()       -> False                           # jar: 0, nothing taken
    clock moves on 0.75 s                              # jar: 1.5
    b.allow()       -> True                            # jar: 0.5
    b.retry_after() -> 0.25                            # 0.5 more token at 2/s

Requirements
------------
- TokenBucket(capacity, rate, clock=time.monotonic). The jar starts full.
  capacity <= 0 or rate <= 0 raises ValueError.
- allow(cost=1) -> bool. True spends `cost` tokens; False spends nothing.
  cost <= 0 raises ValueError.
- tokens() -> float: the level right now. Spends nothing.
- retry_after(cost=1) -> float: seconds until allow(cost) would succeed if
  nothing else happens. 0.0 if it would succeed now; math.inf if cost is
  bigger than capacity (it can never succeed). Spends nothing.
- Refill is lazy: work it out from the time since you last looked. No timer,
  no thread, no sleep, no loop that adds one token at a time. A bucket left
  alone for a billion seconds must answer instantly.
- If the clock ever reads earlier than last time, treat that as no time
  passing (never take tokens away), and measure from the new reading on.
- Read the clock at most once per method call. Use the `clock` you were
  given; never time.time() (section 8 of the chapter says why).
- O(1) time and O(1) memory: the bucket must not grow with the number of
  requests.

Target: O(1) per call, O(1) memory.

Before you code (say it out loud)
---------------------------------
1. Which knob sets the burst, and which sets the long-run rate? Over any
   T seconds, at most how many cost-1 requests can pass?
2. Why compute the refill on each call instead of running a timer? Price
   the timer version at 1 million keys.
3. Why time.monotonic and not time.time? What does a 30-second backwards
   jump do to a bucket that uses time.time?
4. Compare with the sliding window counter and the leaky bucket: when would
   you pick each?

Follow-up: make it thread-safe (section 03), then share it across servers
(chapter section 9: one Lua script in Redis).

Run:  python3 -m pytest -k token_bucket
"""

import time
from typing import Callable


class TokenBucket:
    def __init__(self, capacity: float, rate: float,
                 clock: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def allow(self, cost: float = 1) -> bool:
        raise NotImplementedError

    def tokens(self) -> float:
        raise NotImplementedError

    def retry_after(self, cost: float = 1) -> float:
        raise NotImplementedError
