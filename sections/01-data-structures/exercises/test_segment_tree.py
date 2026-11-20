import math
import operator
import random
import signal
from functools import reduce

import pytest

from segment_tree import SegmentTree


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second with O(log n) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: does a query or update visit the whole list?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Counted:
    """Wrap a combine function and count its calls."""

    def __init__(self, fn):
        self.fn, self.calls = fn, 0

    def __call__(self, a, b):
        self.calls += 1
        return self.fn(a, b)


def brute(a, lo, hi, fn, ident):
    return reduce(fn, a[lo:hi], ident)


def test_example():
    t = SegmentTree([5, 2, 9, 1, 4], min, float("inf"))
    assert len(t) == 5
    assert t.query(1, 4) == 1
    t.update(3, 7)
    assert t.query(2, 5) == 4
    s = SegmentTree(["a", "b", "c", "d"], lambda x, y: x + y, "")
    assert s.query(1, 4) == "bcd"


def test_empty_and_single():
    t = SegmentTree([], operator.add, 0)
    assert len(t) == 0 and t.query(0, 0) == 0
    u = SegmentTree([42], max, float("-inf"))
    assert u.query(0, 1) == 42 and u.query(0, 0) == float("-inf") and u.query(1, 1) == float("-inf")
    u.update(0, -5)
    assert u.query(0, 1) == -5


def test_empty_ranges_give_identity():
    t = SegmentTree([3, 1, 4, 1, 5], operator.add, 0)
    assert [t.query(i, i) for i in range(6)] == [0] * 6


def test_bad_index_raises():
    t = SegmentTree([1, 2, 3], operator.add, 0)
    for i in (-1, 3, 7):
        with pytest.raises(IndexError):
            t.update(i, 9)
    assert t.query(0, 3) == 6


def test_update_replaces_not_adds():
    t = SegmentTree([5, 5, 5], operator.add, 0)
    t.update(1, 2)
    t.update(1, 2)
    assert t.query(0, 3) == 12


@pytest.mark.parametrize("name", ["sum", "min", "max"])
def test_random_against_brute_force(name):
    fn, ident = {"sum": (operator.add, 0), "min": (min, float("inf")), "max": (max, float("-inf"))}[name]
    rng = random.Random({"sum": 31, "min": 32, "max": 33}[name])
    for _ in range(60):
        n = rng.randint(1, 37)  # not just powers of two
        a = [rng.randint(-20, 20) for _ in range(n)]
        t = SegmentTree(a, fn, ident)
        for _ in range(60):
            if rng.random() < 0.4:
                i, v = rng.randrange(n), rng.randint(-20, 20)
                a[i] = v
                t.update(i, v)
            else:
                lo = rng.randint(0, n)
                hi = rng.randint(lo, n)
                assert t.query(lo, hi) == brute(a, lo, hi, fn, ident), (name, a, lo, hi)


def test_order_is_kept_left_to_right():
    rng = random.Random(21)
    for _ in range(40):
        n = rng.randint(1, 30)
        a = [chr(97 + rng.randrange(26)) for _ in range(n)]
        t = SegmentTree(a, lambda x, y: x + y, "")
        for _ in range(40):
            if rng.random() < 0.3:
                i = rng.randrange(n)
                a[i] = chr(65 + rng.randrange(26))
                t.update(i, a[i])
            lo = rng.randint(0, n)
            hi = rng.randint(lo, n)
            assert t.query(lo, hi) == "".join(a[lo:hi]), (a, lo, hi)


def test_does_not_keep_a_reference_to_the_callers_list():
    a = [1, 2, 3, 4]
    t = SegmentTree(a, operator.add, 0)
    a[0] = 100
    assert t.query(0, 4) == 10
    t.update(1, 20)
    assert a == [100, 2, 3, 4]


def test_build_is_linear():
    n = 50_000
    rng = random.Random(7)
    a = [rng.randint(0, 1000) for _ in range(n)]
    c = Counted(operator.add)
    t = SegmentTree(a, c, 0)
    assert c.calls < 2 * n, f"{c.calls:,} combine calls to build {n:,} items: each internal node needs one"
    assert t.query(0, n) == sum(a)


def test_query_costs_log_n():
    n = 50_000
    rng = random.Random(8)
    a = [rng.randint(-1000, 1000) for _ in range(n)]
    c = Counted(min)
    t = SegmentTree(a, c, float("inf"))
    m = 2000
    budget = m * (4 * math.log2(n) + 4)
    c.calls = 0
    for _ in range(m):
        lo = rng.randrange(n)
        hi = rng.randint(lo + 1, n)
        assert t.query(lo, hi) == min(a[lo:hi])
    assert c.calls <= budget, f"{c.calls:,} combine calls for {m:,} queries (budget {budget:,.0f}): a query should use whole blocks, a few per level"


def test_update_costs_log_n():
    n = 50_000
    rng = random.Random(9)
    a = [rng.randint(-1000, 1000) for _ in range(n)]
    c = Counted(operator.add)
    t = SegmentTree(a, c, 0)
    m = 2000
    budget = m * (2 * math.log2(n) + 4)
    c.calls = 0
    for _ in range(m):
        i, v = rng.randrange(n), rng.randint(-1000, 1000)
        a[i] = v
        t.update(i, v)
    assert c.calls <= budget, f"{c.calls:,} combine calls for {m:,} updates (budget {budget:,.0f}): only the blocks that contain item i change"
    assert t.query(0, n) == sum(a)
