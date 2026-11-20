import math
import random
import signal

import pytest

from interval_sweep import count_at, covered_at_least, min_rooms


@pytest.fixture(autouse=True)
def time_limit(request):
    """Each test takes well under a second with the intended approach (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something checking every interval for every moment?")

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


def random_intervals(rng, n, lo=0, hi=60, longest=15):
    out = []
    for _ in range(n):
        s = rng.randint(lo, hi)
        out.append((s, s + rng.randint(1, longest)))
    return out


def depth_per_cell(intervals):
    """Brute force for integer times: how many intervals cover each unit cell [t, t + 1)."""
    d = {}
    for s, e in intervals:
        for t in range(s, e):
            d[t] = d.get(t, 0) + 1
    return d


# 1. min_rooms
def test_rooms_examples():
    assert min_rooms([(0, 30), (5, 10), (15, 20)]) == 2
    assert min_rooms([(9, 10), (10, 11)]) == 1, "a meeting that ends at 10 frees its room for one that starts at 10"
    assert min_rooms([]) == 0
    assert min_rooms([(1, 2)]) == 1
    assert min_rooms([(1, 5), (1, 5), (1, 5)]) == 3
    assert min_rooms([(1, 4), (2, 5), (3, 6), (4, 7)]) == 3
    assert min_rooms([(5, 8), (1, 3), (2, 6)]) == 2


def test_rooms_ties_at_the_same_time():
    # three meetings end at 10 and three start at 10: never more than 3 at once
    assert min_rooms([(8, 10), (9, 10), (7, 10), (10, 12), (10, 11), (10, 13)]) == 3
    assert min_rooms([(10, 11), (10, 12), (9, 10)]) == 2


def test_rooms_random():
    rng = random.Random(1)
    for _ in range(400):
        data = random_intervals(rng, rng.randint(0, 25))
        want = max(depth_per_cell(data).values(), default=0)
        assert min_rooms(data) == want, data


def test_rooms_does_not_modify_input():
    data = [(5, 6), (1, 3), (2, 4)]
    min_rooms(data)
    assert data == [(5, 6), (1, 3), (2, 4)]


def test_rooms_comparisons():
    n = 2000
    data = random_intervals(random.Random(2), n, 0, 50_000, 400)
    want = max(depth_per_cell(data).values())
    C.cmps = 0
    got = min_rooms([(C(s), C(e)) for s, e in data])
    assert got == want
    budget = 6 * n * math.log2(n) + 20 * n
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} meetings (budget {budget:,.0f}): sort the events once and sweep"


# 2. covered_at_least
def test_covered_examples():
    data = [(0, 10), (5, 15), (8, 9)]
    assert covered_at_least(data, 1) == 15
    assert covered_at_least(data, 2) == 5
    assert covered_at_least(data, 3) == 1
    assert covered_at_least(data, 4) == 0
    assert covered_at_least([], 1) == 0
    assert covered_at_least([(1, 3), (3, 5)], 1) == 4
    assert covered_at_least([(1, 3), (3, 5)], 2) == 0, "touching is not overlapping"
    assert covered_at_least([(0, 4), (0, 4)], 2) == 4


def test_covered_random():
    rng = random.Random(3)
    for _ in range(400):
        data = random_intervals(rng, rng.randint(0, 20))
        k = rng.randint(1, 4)
        want = sum(1 for c in depth_per_cell(data).values() if c >= k)
        assert covered_at_least(data, k) == want, (data, k)


def test_covered_fractions_and_huge_times():
    assert covered_at_least([(0.5, 2.0), (1.5, 3.0)], 2) == 0.5
    big = 10 ** 15  # far too many unit cells to mark one by one
    assert covered_at_least([(0, big), (big // 2, 2 * big)], 2) == big // 2
    assert covered_at_least([(0, big), (big // 2, 2 * big)], 1) == 2 * big


def test_covered_comparisons():
    n = 2000
    data = random_intervals(random.Random(4), n, 0, 50_000, 400)
    d = depth_per_cell(data)
    C.cmps = 0
    got = covered_at_least([(C(s), C(e)) for s, e in data], 3)
    assert got == sum(1 for c in d.values() if c >= 3)
    budget = 6 * n * math.log2(n) + 20 * n
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} intervals (budget {budget:,.0f}): sort the events once and sweep"


# 3. count_at
def brute_count(intervals, times):
    return [sum(1 for s, e in intervals if s <= t < e) for t in times]


def test_count_examples():
    assert count_at([(1, 5), (2, 3), (4, 8)], [0, 2, 3, 4, 8]) == [0, 2, 1, 2, 0]
    assert count_at([], [1, 2]) == [0, 0]
    assert count_at([(1, 2)], []) == []
    assert count_at([(1, 3), (1, 3)], [3, 1, 2]) == [0, 2, 2], "answers come back in the order of the times"


def test_count_random():
    rng = random.Random(5)
    for _ in range(300):
        data = random_intervals(rng, rng.randint(0, 20))
        times = [rng.randint(-2, 80) for _ in range(rng.randint(0, 15))]
        assert count_at(data, times) == brute_count(data, times), (data, times)


def test_count_comparisons():
    n = q = 2000
    rng = random.Random(6)
    data = random_intervals(rng, n, 0, 50_000, 400)
    times = [rng.randint(0, 50_500) for _ in range(q)]
    want = brute_count(data, times)
    C.cmps = 0
    got = count_at([(C(s), C(e)) for s, e in data], [C(t) for t in times])
    assert got == want
    budget = 6 * (n + q) * math.log2(n + q) + 10 * (n + q)
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} intervals and {q:,} times (budget {budget:,.0f}): sort once, then binary search or sweep"
