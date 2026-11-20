"""
Leaky bucket as a queue (one process)
Topic: 02.14  |  Priority: P2

Problem
-------
Requests pour into a bucket. They leak out of a hole at the bottom at a
steady `rate` per second, one at a time, in arrival order, and only then
reach the server. The bucket holds at most `capacity` waiting requests;
a request that arrives to a full bucket overflows and is rejected.

Leak times: the first request leaks the moment it arrives. Each later
accepted one leaks at max(its arrival time, the previous accepted
request's leak time + 1/rate). So the server never sees two requests
closer together than 1/rate seconds.

A request is "waiting" while its leak time is still in the future. A new
request is accepted if it can leak at once (delay 0), or if fewer than
`capacity` requests are waiting when it arrives. Rejected requests change
nothing.

    b = LeakyBucket(rate=2, capacity=3, clock=clock)    # one leak per 0.5 s
    t=0    offer("a") -> 0.0     leaks at 0.0 (straight through)
    t=0    offer("b") -> 0.5     leaks at 0.5   waiting: b
    t=0    offer("c") -> 1.0     leaks at 1.0   waiting: b, c
    t=0    offer("d") -> 1.5     leaks at 1.5   waiting: b, c, d
    t=0    offer("e") -> None    3 waiting: full, rejected
    t=0    poll()     -> ["a"]
    t=1.2  poll()     -> ["b", "c"]
    t=1.2  waiting()  -> 1       (d)
    t=1.2  offer("f") -> 0.8     leaks at 2.0

Requirements
------------
- LeakyBucket(rate, capacity, clock=time.monotonic). rate <= 0 or
  capacity < 0 raises ValueError. (capacity 0: only requests that can leak
  at once get through.)
- offer(item) -> float | None: the delay (leak time - now) if accepted,
  None if the bucket is full.
- poll() -> list: every item whose leak time is <= now and that poll has
  not returned before, in arrival order.
- waiting() -> int: accepted items whose leak time is > now.
- Everything is worked out from the clock when a method is called: no
  timer, no thread, no sleep. Read the clock at most once per call.
- Amortized O(1) per call (plus the size of poll's answer), even with a
  huge capacity and with poll() called rarely: never walk the queue, or
  the leaked-but-not-polled items at its front, to count it.

Target: amortized O(1) per call; memory O(capacity + items not yet polled).

Before you code (say it out loud)
---------------------------------
1. Token bucket and leaky bucket, same burst of 10 at t=0: what does the
   server see in each case, and what does the client feel?
2. Which items are in your queue: waiting, leaked but not polled, or both?
   How do you count the waiting ones without walking the queue?
3. When is the delay itself a problem? (A user waiting 8 s for a page.)

Run:  python3 -m pytest -k leaky_bucket
"""

import time
from typing import Any, Callable, List, Optional


class LeakyBucket:
    def __init__(self, rate: float, capacity: int,
                 clock: Callable[[], float] = time.monotonic):
        raise NotImplementedError

    def offer(self, item: Any) -> Optional[float]:
        raise NotImplementedError

    def poll(self) -> List[Any]:
        raise NotImplementedError

    def waiting(self) -> int:
        raise NotImplementedError
