"""
Thread-safe bounded producer-consumer queue with graceful shutdown
Topic: 03.05 03.07  |  Priority: P0

Build a blocking bounded FIFO queue from scratch using threading.Lock /
threading.Condition and collections.deque (do NOT wrap queue.Queue).

API
---
class QueueClosed(Exception):
    Raised by put() when the queue is closed, and by get() once the queue is
    closed AND empty.

class BoundedQueue:
    __init__(self, capacity: int)
        capacity < 1 raises ValueError.

    put(self, item) -> None
        Block while the queue is full and open. If closed before (or while)
        waiting, raise QueueClosed. Otherwise append item and wake a waiter.

    get(self) -> Any
        Block while the queue is empty and open. If items remain (even after
        close()), pop and return the oldest item in FIFO order and wake a
        waiting producer. If empty and closed, raise QueueClosed.

    close(self) -> None
        Mark the queue closed (idempotent) and wake ALL waiting producers and
        consumers so no thread hangs at shutdown.

    __len__(self) -> int
        Current number of buffered items (thread-safe).

What the tests measure
----------------------
- Strict FIFO ordering and exact delivery across 8 producers x 8 consumers
  (zero lost or duplicated items).
- Backpressure: producers genuinely block when len == capacity until a consumer
  drains an item.
- Graceful shutdown: consumers drain remaining buffered items after close(),
  then raise QueueClosed; blocked producers and consumers wake up cleanly
  instead of deadlocking.

Before you code (say it out loud)
---------------------------------
1. Why must Condition.wait() ALWAYS sit inside a `while` loop, never an `if`?
2. Why does close() need notify_all() rather than notify()?
3. If you use two Conditions (not_full and not_empty), why must they share the
   exact same underlying Lock?

Run:  python3 -m pytest -k bounded_queue
"""


class QueueClosed(Exception):
    pass


class BoundedQueue:
    def __init__(self, capacity):
        raise NotImplementedError

    def put(self, item):
        raise NotImplementedError

    def get(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError
