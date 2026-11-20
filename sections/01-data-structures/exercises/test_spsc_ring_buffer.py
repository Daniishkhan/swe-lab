import gc
import random
import signal
import threading
import time
import weakref
from collections import deque

import pytest

from spsc_ring_buffer import EMPTY, SPSCRingBuffer


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second with O(1) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 20 s: is a thread spinning forever, or is an operation O(n)?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---- Instruments -----------------------------------------------------------
# ROLE says which side is running right now: "push" inside try_push, "pop"
# inside try_pop, "out" otherwise. A single-threaded test can then check who
# reads and writes what, at the exact moment it happens.
ROLE = ["out"]
READS = {"head": 0, "tail": 0}  # head read by try_push, tail read by try_pop
WRITES = []  # (role, attribute name)


def raw(obj, name):
    return object.__getattribute__(obj, name)


class Watched(SPSCRingBuffer):
    def __getattribute__(self, name):
        if name == "head" and ROLE[0] == "push":
            READS["head"] += 1
        elif name == "tail" and ROLE[0] == "pop":
            READS["tail"] += 1
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        WRITES.append((ROLE[0], name))
        object.__setattr__(self, name, value)

    def try_push(self, item):
        ROLE[0] = "push"
        try:
            return super().try_push(item)
        finally:
            ROLE[0] = "out"

    def try_pop(self):
        ROLE[0] = "pop"
        try:
            return super().try_pop()
        finally:
            ROLE[0] = "out"


class RecordingSlots(list):
    """Stands in for rb.slots and checks each slot access against the
    counters at the moment it happens."""

    def __init__(self, ring, data):
        super().__init__(data)
        self.ring, self.problems, self.writes, self.reads = ring, [], 0, 0

    def _counters(self):
        return raw(self.ring, "head"), raw(self.ring, "tail"), len(self) - 1

    def __setitem__(self, i, v):
        head, tail, mask = self._counters()
        if ROLE[0] == "push":
            self.writes += 1
            if i != (tail & mask):
                self.problems.append(f"producer wrote slot {i}, but tail is {tail} (slot {tail & mask}): "
                                     "was tail advanced before the item was written?")
        elif ROLE[0] == "pop":
            if v is not None:
                self.problems.append("the consumer may only clear a slot (set it to None)")
            if i != (head & mask):
                self.problems.append(f"consumer cleared slot {i}, but head is {head} (slot {head & mask}): "
                                     "was head advanced before the slot was cleared? The producer may already own it.")
        super().__setitem__(i, v)

    def __getitem__(self, i):
        head, tail, mask = self._counters()
        if ROLE[0] == "pop":
            self.reads += 1
            if i != (head & mask) or tail == head:
                self.problems.append(f"consumer read slot {i} with head {head}, tail {tail}: "
                                     "read the item before advancing head, and only when tail > head")
        return super().__getitem__(i)


@pytest.fixture
def watched():
    ROLE[0] = "out"
    READS.update(head=0, tail=0)
    WRITES.clear()
    return Watched


# ---- Behavior -------------------------------------------------------------
def test_example():
    rb = SPSCRingBuffer(4)
    assert rb.try_push("a") and rb.try_push("b")
    assert len(rb) == 2
    assert rb.try_pop() == "a" and rb.try_pop() == "b"
    assert rb.try_pop() is EMPTY
    assert len(rb) == 0


def test_capacity_must_be_a_power_of_two():
    for bad in (0, 3, 6, 12, 100, -4):
        with pytest.raises(ValueError):
            SPSCRingBuffer(bad)
    for good in (1, 2, 8, 1024):
        assert len(SPSCRingBuffer(good).slots) == good


def test_full_and_empty():
    rb = SPSCRingBuffer(2)
    assert rb.try_pop() is EMPTY
    assert rb.try_push(1) and rb.try_push(2)
    assert rb.try_push(3) is False, "a ring of 2 holds exactly 2: no slot is wasted"
    assert len(rb) == 2
    assert rb.try_pop() == 1
    assert rb.try_push(3)
    assert [rb.try_pop(), rb.try_pop()] == [2, 3]
    assert rb.try_pop() is EMPTY


def test_capacity_one():
    rb = SPSCRingBuffer(1)
    for i in range(5):
        assert rb.try_push(i) and not rb.try_push("x")
        assert rb.try_pop() == i and rb.try_pop() is EMPTY


def test_none_is_a_legal_item():
    rb = SPSCRingBuffer(4)
    assert rb.try_push(None) and rb.try_push(0)
    assert len(rb) == 2
    first = rb.try_pop()
    assert first is None and first is not EMPTY, "None was pushed, so None must come out: decide 'empty' from the counters"
    assert rb.try_pop() == 0 and rb.try_pop() is EMPTY


def test_layout_counters_and_slots():
    rb = SPSCRingBuffer(4)
    slots = rb.slots
    assert slots == [None] * 4 and rb.head == 0 and rb.tail == 0
    for s in range(10):  # wrap around the ring twice
        assert rb.try_push(f"item{s}")
        assert rb.slots[s & 3] == f"item{s}", f"item number {s} must sit in slots[{s} & 3]"
        assert rb.tail == s + 1 and rb.head == s
        assert rb.try_pop() == f"item{s}"
        assert rb.head == s + 1
        assert rb.slots[s & 3] is None, "clear the slot when you pop"
    assert rb.slots is slots and len(slots) == 4, "self.slots is made once and never replaced"


def test_matches_a_deque_on_random_operations():
    rng = random.Random(14)
    for cap in (1, 2, 4, 8, 16):
        rb, ref = SPSCRingBuffer(cap), deque()
        for _ in range(3000):
            if rng.random() < 0.55:
                x = rng.choice([None, rng.randint(-50, 50), "s"])
                ok = rb.try_push(x)
                assert ok == (len(ref) < cap)
                if ok:
                    ref.append(x)
            else:
                got = rb.try_pop()
                if ref:
                    assert got == ref.popleft()
                else:
                    assert got is EMPTY
            assert len(rb) == len(ref)
            assert rb.tail - rb.head == len(ref)


def test_popped_items_are_not_kept_alive():
    class Big:
        pass

    rb = SPSCRingBuffer(8)
    obj = Big()
    ref = weakref.ref(obj)
    rb.try_push(obj)
    del obj
    rb.try_pop()  # result thrown away
    gc.collect()
    assert ref() is None, "the ring still holds the popped object: set its slot back to None"


# ---- Who writes what, and in which order ------------------------------------
def test_each_counter_has_one_writer(watched):
    rb = watched(8)
    rng = random.Random(3)
    for _ in range(2000):
        if rng.random() < 0.5:
            rb.try_push(rng.random())
        else:
            rb.try_pop()
    bad_push = {n for role, n in WRITES if role == "push" and n == "head"}
    bad_pop = {n for role, n in WRITES if role == "pop" and n == "tail"}
    assert not bad_push, "try_push assigned self.head: only the consumer may write head"
    assert not bad_pop, "try_pop assigned self.tail: only the producer may write tail"
    assert any(role == "push" and n == "tail" for role, n in WRITES), "try_push must publish by assigning self.tail"
    assert any(role == "pop" and n == "head" for role, n in WRITES), "try_pop must free slots by assigning self.head"


def test_publish_order(watched):
    rb = watched(4)
    rec = RecordingSlots(rb, rb.slots)
    rb.slots = rec
    rng = random.Random(5)
    expect = deque()
    for i in range(3000):
        if rng.random() < 0.5:
            if rb.try_push(i):
                expect.append(i)
        else:
            got = rb.try_pop()
            assert got == (expect.popleft() if expect else EMPTY)
        assert not rec.problems, rec.problems[0]
    assert rec.writes > 0 and rec.reads > 0, "read and write items through self.slots[...]"


def test_reads_of_the_other_counter_are_rare(watched):
    cap, rounds = 64, 300
    rb = watched(cap)
    for r in range(rounds):
        for i in range(cap):
            assert rb.try_push((r, i))
        for i in range(cap):
            assert rb.try_pop() == (r, i)
    assert READS["head"] <= 2 * rounds, (
        f"try_push read head {READS['head']:,} times in {rounds} rounds of {cap} pushes: "
        "keep a cached copy and re-read head only when the copy says the ring is full")
    assert READS["tail"] <= 2 * rounds, (
        f"try_pop read tail {READS['tail']:,} times in {rounds} rounds of {cap} pops: "
        "keep a cached copy and re-read tail only when the copy says the ring is empty")


def test_full_ring_rereads_head_and_then_sees_space(watched):
    rb = watched(4)
    for i in range(4):
        assert rb.try_push(i)
    assert not rb.try_push("x") and not rb.try_push("x")
    assert rb.try_pop() == 0
    assert rb.try_push(4), "after a pop the producer must notice the free slot (re-read head when the cache says full)"
    assert [rb.try_pop() for _ in range(5)] == [1, 2, 3, 4, EMPTY]
    assert rb.try_push(5) and rb.try_pop() == 5, "after an empty pop the consumer must notice new items"


# ---- Two real threads -------------------------------------------------------
def test_one_producer_thread_one_consumer_thread():
    rb, n = SPSCRingBuffer(8), 30_000
    got, errors = [], []

    def producer():
        try:
            i = 0
            while i < n:
                if rb.try_push(i):
                    i += 1
                else:
                    time.sleep(0)  # full: let the consumer run
        except Exception as e:  # pragma: no cover - reported below
            errors.append(e)

    def consumer():
        try:
            while len(got) < n:
                x = rb.try_pop()
                if x is EMPTY:
                    time.sleep(0)  # empty: let the producer run
                else:
                    got.append(x)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = [threading.Thread(target=producer, daemon=True), threading.Thread(target=consumer, daemon=True)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(15)
    assert not errors, errors[0]
    assert not any(t.is_alive() for t in threads), f"stuck after {len(got):,} of {n:,} items"
    assert got == list(range(n)), "items lost, repeated or out of order"
    assert len(rb) == 0
