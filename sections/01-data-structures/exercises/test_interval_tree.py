import math
import random
import signal

import pytest

from interval_tree import IntervalTree


@pytest.fixture(autouse=True)
def time_limit(request):
    """Each test takes well under a second with the intended approach (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is overlapping() visiting every node, or did sorted adds build a chain?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class C:
    """A time value that counts every comparison made with it (class-wide).
    Subtracting two of them gives a plain number, so lengths still work."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        C.cmps += 1
        return other.v if isinstance(other, C) else other

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __eq__(self, o): return self.v == self._o(o)
    def __ne__(self, o): return self.v != self._o(o)
    def __hash__(self): return hash(self.v)
    def __sub__(self, o): return self.v - (o.v if isinstance(o, C) else o)
    def __rsub__(self, o): return o - self.v
    def __repr__(self): return f"C({self.v})"


def wrap(intervals):
    return [(C(s), C(e)) for s, e in intervals]


def unwrap(intervals):
    return [(s.v, e.v) for s, e in intervals]


def brute(stored, a, b):
    return sorted((s, e) for s, e in stored if s < b and a < e)


def plain(got):
    return sorted((s.v, e.v) if isinstance(s, C) else (s, e) for s, e in got)


def random_intervals(rng, n, span=1_000_000):
    out = []
    for _ in range(n):
        s = rng.randrange(span)
        length = rng.randint(1000, 50_000) if rng.random() < 0.1 else rng.randint(1, 200)
        out.append((s, s + length))
    return out


def test_example():
    t = IntervalTree([(5, 20), (10, 30), (12, 15), (17, 19), (30, 40)])
    assert sorted(t.overlapping(14, 16)) == [(5, 20), (10, 30), (12, 15)]
    t.add(15, 16)
    assert sorted(t.overlapping(14, 16)) == [(5, 20), (10, 30), (12, 15), (15, 16)]
    assert t.overlapping(40, 50) == []
    assert len(t) == 6


def test_edges():
    t = IntervalTree()
    assert len(t) == 0 and t.overlapping(0, 100) == []
    t.add(3, 5)
    assert t.overlapping(5, 6) == [], "half-open: [3, 5) and [5, 6) don't overlap"
    assert t.overlapping(0, 3) == []
    assert t.overlapping(4, 5) == [(3, 5)]
    t.add(3, 5)
    assert sorted(t.overlapping(0, 10)) == [(3, 5), (3, 5)], "duplicates are kept"
    assert len(t) == 2
    one = IntervalTree([(1, 2)])
    assert one.overlapping(0, 10) == [(1, 2)] and len(one) == 1


def test_does_not_modify_input():
    data = [(5, 6), (1, 3), (2, 4)]
    IntervalTree(data)
    assert data == [(5, 6), (1, 3), (2, 4)]


def test_long_interval_that_started_early():
    # the case that breaks "sorted by start, stop scanning early"
    data = [(0, 1000)] + [(i, i + 1) for i in range(1, 500, 2)]
    t = IntervalTree(data)
    assert sorted(t.overlapping(998, 999)) == [(0, 1000)]
    assert sorted(t.overlapping(600, 601)) == [(0, 1000)]


def test_random_against_brute_force():
    rng = random.Random(1)
    for _ in range(150):
        start = [(s, s + rng.randint(1, 15)) for s in (rng.randint(0, 60) for _ in range(rng.randint(0, 25)))]
        t = IntervalTree(start)
        stored = list(start)
        for _ in range(20):
            if rng.random() < 0.4:
                s = rng.randint(0, 60)
                iv = (s, s + rng.randint(1, 15))
                t.add(*iv)
                stored.append(iv)
            a = rng.randint(-5, 80)
            b = a + rng.randint(1, 20)
            assert sorted(t.overlapping(a, b)) == brute(stored, a, b), (stored, a, b)
            assert len(t) == len(stored)


def check_queries(t, stored, n, rng):
    span = 1_000_000
    kinds = {
        "near the left edge": lambda: rng.randrange(0, 2000),
        "past the right edge": lambda: rng.randrange(span + 60_000, span + 80_000),
        "in the middle": lambda: rng.randrange(span),
    }
    for kind, pick in kinds.items():
        for _ in range(40):
            a = pick()
            b = a + rng.randint(1, 50)
            C.cmps = 0
            got = t.overlapping(C(a), C(b))
            used = C.cmps
            want = brute(stored, a, b)
            assert plain(got) == want, (kind, a, b)
            budget = 6 * (len(want) + 1) * math.log2(n)
            assert used <= budget, f"query [{a}, {b}) {kind} found {len(want)} and used {used:,} comparisons (budget {budget:,.0f}): skip subtrees whose max_end <= start, and right subtrees of nodes whose start >= end"


def test_queries_skip_subtrees():
    n = 20_000
    rng = random.Random(2)
    data = random_intervals(rng, n)
    t = IntervalTree([(C(s), C(e)) for s, e in data])
    check_queries(t, data, n, rng)


def test_built_from_sorted_input_is_balanced():
    n = 20_000
    rng = random.Random(3)
    data = sorted(random_intervals(rng, n))
    t = IntervalTree([(C(s), C(e)) for s, e in data])
    check_queries(t, data, n, rng)


def test_adds_keep_max_end_and_stay_cheap():
    n = 20_000
    rng = random.Random(4)
    data = random_intervals(rng, n)
    t = IntervalTree()
    C.cmps = 0
    for s, e in data:
        t.add(C(s), C(e))
    used = C.cmps
    budget = 6 * n * math.log2(n)
    assert used <= budget, f"{used:,} comparisons for {n:,} adds (budget {budget:,.0f}): one walk down from the root per add"
    assert len(t) == n
    # random insert order gives a tree about 2-3 times deeper than perfect, so allow more per query
    for _ in range(60):
        a = rng.randrange(1_000_000)
        b = a + rng.randint(1, 50)
        C.cmps = 0
        got = t.overlapping(C(a), C(b))
        want = brute(data, a, b)
        assert plain(got) == want
        assert C.cmps <= 18 * (len(want) + 1) * math.log2(n), f"{C.cmps:,} comparisons after adds: is add() keeping max_end up to date?"
