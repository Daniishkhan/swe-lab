"""
RingDeque: a double-ended queue on a ring buffer
Topic: 01.02  |  Priority: P0

Problem
-------
Build sections 7 and 8 of the chapter. Store the items in a Python list used
as a fixed row of slots (`self.buf`), plus `self.head` (the slot of the
first item, always in 0..len(self.buf) - 1) and a size. The tests look inside: item i must sit in
self.buf[(self.head + i) % len(self.buf)]. Never shift items: move `head` instead, and wrap
around with % len(self.buf). Grow only when you must: when append or
appendleft finds every slot already full, first make a list twice as big
and copy the items over in line order, starting from head, then add.

    d = RingDeque()
    d.append(1); d.append(2); d.appendleft(0)   # 0, 1, 2
    d[0] -> 0,  d[-1] -> 2,  len(d) -> 3
    d.popleft() -> 0,  d.pop() -> 2

Requirements
------------
- RingDeque(capacity=4): starting number of slots (at least 1).
- append(x), appendleft(x): add at the back / front.
- pop(), popleft(): remove and return from the back / front; raise
  IndexError when empty.
- d[i]: the i-th item from the front, with negative indexes like a list
  (-1 is the back). Raise IndexError out of range.
- len(d), and iter(d) from front to back.
- self.copies: the total number of items copied while growing. Count one per
  item moved into a new, bigger list.
- Target: O(1) for every operation (amortized for the two appends).
- Don't use collections.deque, list.insert(0, ...) or list.pop(0) inside.

What the tests measure
----------------------
200,000 appendlefts in a row must finish fast (a list with insert(0, x)
needs about 5 seconds and hits a time cap), the items must really sit in
the ring (checked through self.buf and self.head), growth must double
(x1.5 is also amortized O(1), but these tests expect x2) and copy fewer
than 2 items per append, and 200,000 random index reads must be fast (a linked list
would walk to each one).

Before you code (say it out loud)
---------------------------------
1. Where does append write? Where does appendleft write, and how does head
   change? Check both with head = 0.
2. Why must the copy during growth start at head and not at slot 0?
3. Why does doubling make growth amortized O(1), when one growth is O(n)?

Run:  pytest -k ring_deque
"""


class RingDeque:
    def __init__(self, capacity: int = 4):
        raise NotImplementedError

    def append(self, x) -> None:
        raise NotImplementedError

    def appendleft(self, x) -> None:
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError

    def popleft(self):
        raise NotImplementedError

    def __getitem__(self, i: int):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError
