"""
Lock-free MPMC queue (Michael and Scott), on simulated threads
Topic: 01.14  |  Priority: P2

Problem
-------
Build section 8 of the chapter: an unbounded queue that any number of
producers and consumers share with no lock, using only compare-and-swap
(CAS). It is the algorithm behind Java's ConcurrentLinkedQueue.

Python gives you no CAS instruction, and the GIL hides most interleavings,
so this exercise simulates threads instead. Every access to shared memory
goes through an AtomicRef (below), and each access is a `yield from`:

    last = yield from self.tail.load()
    ok = yield from last.next.cas(None, node)

Each `yield` is a point where the tests' scheduler may switch to another
"thread". enqueue and dequeue are therefore generators. The scheduler
interleaves them however it likes (seeded random orders, and threads paused
forever in the middle of an operation). Alone, run() drives one to the end:

    q = MSQueue()
    run(q.enqueue("a")); run(q.enqueue("b"))
    run(q.dequeue()) -> "a";  run(q.dequeue()) -> "b"
    run(q.dequeue()) is EMPTY -> True

Layout (the tests look inside, through peek(), which doesn't yield):
- a singly linked list of Node objects that always starts with a dummy
  node; the items are in the nodes after it, oldest first;
- self.head: an AtomicRef to the dummy node;
- self.tail: an AtomicRef to the last node, or, for a moment, the one just
  before it (the tail may lag one step behind; anyone may fix it).

Requirements
------------
- enqueue(value): link a new node after the last node with ONE CAS on that
  node's `next` (from None to the new node). Then try once to swing
  self.tail forward to it. If that second CAS fails, someone helped: fine.
- If enqueue finds the tail lagging (tail's node already has a next), it
  must help: CAS self.tail forward, then retry. Never wait for the thread
  that linked the node to come back.
- dequeue(): return the oldest value and make its node the new dummy, with
  one CAS on self.head; or return EMPTY if the queue is empty. If the queue
  looks non-empty but tail still points at the dummy, help swing the tail
  first (otherwise head could move past tail).
- Touch shared state only through AtomicRef.load() and AtomicRef.cas(),
  each with `yield from`. A node's `value` is written once, before the node
  is linked, so reading it needs no yield.
- No locks, no flags that make other threads wait: if a thread stops forever
  at any point inside an operation, every other thread must still finish
  its operations. That is what "lock-free" means.

What the tests measure
----------------------
- Seeded random interleavings of 2 to 6 threads: every value comes out
  exactly once; values from one producer come out in the order it put them
  in; and a dequeue may return EMPTY only if the queue really was empty at
  some moment while it ran.
- Lock-freedom: for every point k where an enqueue or a dequeue could be
  paused, pause it there forever; other threads must then finish each of
  their operations in at most 60 steps. A spin lock, or an enqueue that
  waits for the lagging tail to be fixed by the thread that linked the
  node, runs past that budget.
- An enqueue paused right after its link CAS, with the tail still lagging:
  a dequeue must return its item (the link is the moment the enqueue
  happens) and must leave tail pointing at head, never behind it.
- Work, measured by counting AtomicRef calls: alone, an enqueue costs
  exactly 2 successful CAS and no failed one, and a dequeue 1 CAS, whatever
  the queue's length, with at most 4 loads each. Walking from the head to
  find the end costs one load per item.

Before you code (say it out loud)
---------------------------------
1. Why does the queue start with a dummy node? What would an empty queue
   look like without one?
2. Which single CAS makes an enqueue "happen" (its linearization point)?
   Which one makes a dequeue happen?
3. Why must a thread that finds the tail lagging fix it instead of waiting?
4. In C, why would this algorithm need tagged pointers or hazard pointers
   (the ABA problem), and why doesn't Python (or Java) need them?

Run:  pytest -k mpmc_queue
"""

EMPTY = object()  # dequeue returns this when the queue is empty


class AtomicRef:
    """One shared memory word holding a reference. Provided: don't change it.

    load() and cas() are generators: they yield once, which is the moment
    another thread may run, and then do their work in one atomic step.
    The class-wide counters let the tests measure your work.
    """

    loads = 0
    cas_ok = 0
    cas_failed = 0

    def __init__(self, value=None):
        self._value = value

    def load(self):
        yield  # another thread may run here
        AtomicRef.loads += 1
        return self._value

    def cas(self, expected, new):
        """If the word still holds `expected` (the same object), replace it
        with `new` and return True. Otherwise change nothing, return False."""
        yield  # another thread may run here
        if self._value is expected:
            self._value = new
            AtomicRef.cas_ok += 1
            return True
        AtomicRef.cas_failed += 1
        return False

    def peek(self):
        """Read without yielding or counting: for tests and debugging only."""
        return self._value

    @classmethod
    def reset_counts(cls):
        cls.loads = cls.cas_ok = cls.cas_failed = 0


class Node:
    """Provided. value is written once, before the node is shared."""

    def __init__(self, value=None):
        self.value = value
        self.next = AtomicRef(None)


def run(op):
    """Run one operation (a generator) alone, to the end, and return its result."""
    try:
        while True:
            next(op)
    except StopIteration as done:
        return done.value


class MSQueue:
    def __init__(self):
        raise NotImplementedError

    def enqueue(self, value):
        raise NotImplementedError
        yield  # (keeps this a generator function)

    def dequeue(self):
        raise NotImplementedError
        yield  # (keeps this a generator function)
