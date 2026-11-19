import random
import signal
from collections import deque

import pytest

from ring_deque import RingDeque


@pytest.fixture(autouse=True)
def time_limit():
    """O(1) operations finish each test in well under a second. Shifting a
    list on every front insert (or walking a linked list to each index)
    takes 5 to 20 seconds on the big tests, so 4 s is a generous line
    (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 4 s: are items shifting (insert(0, x), pop(0)) or is indexing walking?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(4)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def contents(d):
    return [d[i] for i in range(len(d))]


def check_layout(d, start_capacity):
    """The items must really sit in a ring: item i lives in buf[(head + i) % len(buf)],
    and the ring only ever doubles."""
    cap = len(d.buf)
    assert cap >= max(len(d), 1)
    assert cap % start_capacity == 0 and (cap // start_capacity) & (cap // start_capacity - 1) == 0, f"capacity {cap} isn't the start capacity times a power of two"
    for i in range(len(d)):
        assert d[i] is d.buf[(d.head + i) % cap], f"item {i} isn't at buf[(head + {i}) % capacity]"


def test_example():
    d = RingDeque()
    d.append(1)
    d.append(2)
    d.appendleft(0)
    assert len(d) == 3
    assert (d[0], d[1], d[2], d[-1], d[-3]) == (0, 1, 2, 2, 0)
    assert list(d) == [0, 1, 2]
    assert d.popleft() == 0
    assert d.pop() == 2
    assert list(d) == [1]


def test_appendleft_moves_head_not_items():
    d = RingDeque(8)
    for x in "abc":
        d.append(x)
    before, head = list(d.buf), d.head
    d.appendleft("z")
    assert d.head == (head - 1) % 8, "appendleft should step head back one slot (wrapping), not shift the items"
    changed = [i for i in range(8) if d.buf[i] is not before[i]]
    assert changed == [d.head], f"appendleft changed slots {changed}: it should write exactly one slot"


def test_empty_and_bad_index():
    d = RingDeque()
    assert len(d) == 0 and list(d) == []
    for op in (d.pop, d.popleft):
        with pytest.raises(IndexError):
            op()
    with pytest.raises(IndexError):
        d[0]
    d.append("x")
    for i in (1, -2, 5):
        with pytest.raises(IndexError):
            d[i]
    assert d.pop() == "x"
    with pytest.raises(IndexError):
        d.popleft()


def test_capacity_one_and_none_values():
    d = RingDeque(capacity=1)
    d.append(None)
    d.appendleft(None)
    d.append(3)
    assert list(d) == [None, None, 3]
    assert d.popleft() is None and d.popleft() is None and d.popleft() == 3


def test_wraps_without_growing():
    """Fill, drain from the front, refill: the back must wrap to slot 0."""
    d = RingDeque(capacity=4)
    for x in "ABC":
        d.append(x)
    assert d.popleft() == "A" and d.popleft() == "B"
    for x in "DEF":
        d.append(x)  # C at slot 2, then D, E wrap to slots 3, 0, 1
    assert list(d) == list("CDEF")
    assert d.copies == 0, "4 items fit in 4 slots: nothing should have been copied yet"
    d.append("G")  # full: grow, copying C, D, E, F in line order
    assert list(d) == list("CDEFG")
    assert d.copies == 4
    check_layout(d, 4)


def test_matches_collections_deque():
    rng = random.Random(12)
    for trial in range(40):
        cap0 = rng.randint(1, 5)
        d, ref = RingDeque(capacity=cap0), deque()
        for step in range(rng.randint(0, 400)):
            op = rng.random()
            if op < 0.3:
                d.append(step)
                ref.append(step)
            elif op < 0.6:
                d.appendleft(step)
                ref.appendleft(step)
            elif op < 0.8 and ref:
                assert d.pop() == ref.pop()
            elif ref:
                assert d.popleft() == ref.popleft()
            assert len(d) == len(ref)
            if ref:
                i = rng.randrange(-len(ref), len(ref))
                assert d[i] == ref[i], (trial, step, i)
        assert list(d) == list(ref) == contents(d)
        check_layout(d, cap0)


def test_front_inserts_are_constant_time_and_growth_is_by_a_multiple():
    n = 200_000
    d = RingDeque()
    for i in range(n):
        d.appendleft(i)
    assert len(d) == n
    assert d[0] == n - 1 and d[-1] == 0 and d[n // 2] == n - 1 - n // 2
    assert d.copies < 2 * n, f"{d.copies:,} copies for {n:,} appends: grow by doubling, not by a fixed step"
    check_layout(d, 4)


def test_queue_use_stays_fast_and_bounded():
    """A long-running queue: 300,000 enqueues and dequeues with at most 1,000
    waiting. Growth should stop early; no shifting allowed."""
    d = RingDeque()
    for i in range(1_000):
        d.append(i)
    for i in range(1_000, 301_000):
        d.append(i)
        assert d.popleft() == i - 1_000
    assert len(d) == 1_000 and d[0] == 300_000 and d[-1] == 300_999
    assert d.copies < 2_048, f"{d.copies:,} copies, but the queue never held more than 1,001 items"


def test_random_index_reads_are_constant_time():
    n = 200_000
    d = RingDeque()
    for i in range(n):
        d.append(i)
    for _ in range(n // 2):
        d.popleft()
        d.append(n)  # keep the ring wrapped
    rng = random.Random(3)
    for _ in range(200_000):
        i = rng.randrange(n)
        expected = n // 2 + i if i < n // 2 else n
        assert d[i] == expected
