"""
SPSC ring buffer: one producer, one consumer, no lock
Topic: 01.14  |  Priority: P2

Problem
-------
Build sections 5 and 6 of the chapter: a fixed-size ring buffer that one
producer thread and one consumer thread share without any lock. It works
because every shared counter has exactly one writer.

    rb = SPSCRingBuffer(4)
    rb.try_push("a") -> True;  rb.try_push("b") -> True
    len(rb) -> 2
    rb.try_pop() -> "a";  rb.try_pop() -> "b"
    rb.try_pop() is EMPTY -> True

The layout is fixed, because the tests look inside:

- self.slots: a list of exactly `capacity` slots, made once in __init__ and
  never replaced or resized. Every slot starts as None.
- self.tail: how many items were ever pushed. Only try_push writes it.
- self.head: how many items were ever popped. Only try_pop writes it.
- Item number s (counting pushes from 0) lives in self.slots[s & mask],
  where mask = capacity - 1. The counters only grow; they never wrap.

Requirements
------------
- SPSCRingBuffer(capacity): capacity must be a power of two (1, 2, 4, ...),
  otherwise raise ValueError. Then `s % capacity == s & (capacity - 1)`.
- try_push(item) -> bool: False if the ring is full (tail - head == capacity),
  and nothing changes. Otherwise write the item into its slot, and only
  then publish it by advancing self.tail. Never assign self.head.
- try_pop() -> the oldest item, or the module's EMPTY sentinel if there is
  none. Read the item, set its slot back to None (so the ring doesn't keep
  a popped object alive), and only then free the slot by advancing
  self.head. Never assign self.tail. None is a legal item: decide "empty"
  from the counters, never from what a slot holds.
- len(rb): tail - head.
- Reading the other side's counter is the expensive part on real hardware
  (a cache miss on another core, section 4). So each side keeps its own
  cached copy of the other side's counter, and re-reads the real one only
  when the cached copy says "full" (producer) or "empty" (consumer). Keep
  those copies in attributes of your own (any name except head and tail).
- Every operation is O(1). No locks, no collections.deque, no queue.Queue.

What the tests measure
----------------------
- Order of writes, checked at the moment each one happens: the tests swap
  self.slots for a recording list. When the producer writes a slot, tail
  must not have moved yet; when the consumer reads or clears a slot, head
  must not have moved yet. Publishing first is the classic SPSC bug: the
  other thread can see the new counter before the item is there.
- Who writes what: try_push must never assign head, try_pop never tail.
- Reads of the other side's counter: 300 rounds of "push 64, pop 64" on a
  capacity-64 ring must read head (in try_push) and tail (in try_pop) at
  most 2 times per round each. Re-reading on every call costs 64.
- A real producer thread and consumer thread pass 30,000 items through a
  capacity-8 ring: every item must arrive once, in order. (On CPython with
  the GIL this checks the logic, not the hardware memory order; section 6
  explains what C, Java and Rust need on top.)

Before you code (say it out loud)
---------------------------------
1. Why can the producer and the consumer both work without a lock, when two
   producers can't?
2. Why write the slot first and advance tail second? What can the consumer
   see if you swap the two lines?
3. With counters that never wrap, how do you tell "full" from "empty"? Why
   does the classic wrapped-index ring waste one slot?
4. Why cache the other side's counter? When must you re-read it?

Run:  pytest -k spsc_ring_buffer
"""

EMPTY = object()  # try_pop returns this when there is nothing to take


class SPSCRingBuffer:
    def __init__(self, capacity: int):
        raise NotImplementedError

    def try_push(self, item) -> bool:
        raise NotImplementedError

    def try_pop(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
