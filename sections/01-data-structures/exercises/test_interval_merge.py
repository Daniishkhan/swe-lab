import math
import random
import signal

import pytest

from interval_merge import insert, intersect, merge


@pytest.fixture(autouse=True)
def time_limit(request):
    """Each test takes well under a second with the intended approach (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something comparing every pair of intervals?")

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


def cells(intervals):
    """Brute force: the set of unit cells [t, t + 1) covered (integer times)."""
    return {t for s, e in intervals for t in range(s, e)}


def blocks_of(cs):
    """Turn a set of covered unit cells back into sorted, non-touching blocks."""
    out = []
    for t in sorted(cs):
        if out and out[-1][1] == t:
            out[-1][1] = t + 1
        else:
            out.append([t, t + 1])
    return [tuple(b) for b in out]


def random_intervals(rng, n, lo=-30, hi=60, longest=12):
    out = []
    for _ in range(n):
        s = rng.randint(lo, hi)
        out.append((s, s + rng.randint(1, longest)))
    return out


# 1. merge
def test_merge_example():
    assert merge([(8, 10), (1, 3), (2, 6), (15, 18), (6, 7)]) == [(1, 7), (8, 10), (15, 18)]


def test_merge_edges():
    assert merge([]) == []
    assert merge([(4, 5)]) == [(4, 5)]
    assert merge([(1, 3), (3, 5)]) == [(1, 5)], "touching intervals become one block"
    assert merge([(1, 10), (2, 3), (4, 5)]) == [(1, 10)], "the block keeps the max end, not the last end"
    assert merge([(2, 3), (4, 5), (1, 10)]) == [(1, 10)]
    assert merge([(1, 2), (1, 2), (1, 2)]) == [(1, 2)]
    assert merge([(-5, -1), (-3, 0), (2, 4)]) == [(-5, 0), (2, 4)]
    assert merge([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]


def test_merge_does_not_modify_input():
    data = [(5, 6), (1, 3), (2, 4)]
    merge(data)
    assert data == [(5, 6), (1, 3), (2, 4)]


def test_merge_random():
    rng = random.Random(1)
    for _ in range(400):
        data = random_intervals(rng, rng.randint(0, 25))
        assert merge(data) == blocks_of(cells(data)), data


def test_merge_strings():
    assert merge([("b", "d"), ("a", "c"), ("x", "z")]) == [("a", "d"), ("x", "z")]


def test_merge_comparisons():
    n = 2000
    rng = random.Random(2)
    data = random_intervals(rng, n, 0, 100_000, 60)
    want = blocks_of(cells(data))
    items = wrap(data)
    C.cmps = 0
    got = unwrap(merge(items))
    assert got == want
    budget = 4 * n * math.log2(n) + 10 * n
    assert C.cmps <= budget, f"{C.cmps:,} comparisons to merge {n:,} intervals (budget {budget:,.0f}): sort once, then one pass"


# 2. insert
def test_insert_examples():
    assert insert([(1, 3), (6, 9), (12, 15)], (2, 7)) == [(1, 9), (12, 15)]
    assert insert([(1, 3), (6, 9)], (4, 5)) == [(1, 3), (4, 5), (6, 9)]
    assert insert([], (4, 5)) == [(4, 5)]
    assert insert([(1, 3)], (3, 4)) == [(1, 4)], "touching merges"
    assert insert([(5, 6)], (1, 2)) == [(1, 2), (5, 6)]
    assert insert([(5, 6)], (8, 9)) == [(5, 6), (8, 9)]
    assert insert([(1, 2), (4, 5), (7, 8)], (0, 10)) == [(0, 10)]
    assert insert([(1, 10)], (3, 4)) == [(1, 10)]


def test_insert_does_not_modify_input():
    blocks = [(1, 3), (6, 9)]
    insert(blocks, (2, 7))
    assert blocks == [(1, 3), (6, 9)]


def test_insert_random():
    rng = random.Random(3)
    for _ in range(500):
        blocks = blocks_of(cells(random_intervals(rng, rng.randint(0, 10))))
        new = random_intervals(rng, 1, longest=20)[0]
        assert insert(blocks, new) == blocks_of(cells(blocks + [new])), (blocks, new)


def test_insert_comparisons():
    n = 100_000
    blocks = [(C(10 * i), C(10 * i + 5)) for i in range(n)]  # [0,5) [10,15) [20,25) ...
    rng = random.Random(4)
    for _ in range(200):
        s = rng.randrange(10 * n)
        e = s + rng.choice([1, 2, 7, 30, 200])
        lo = max(0, -(-(s - 5) // 10))  # first block whose end >= s
        hi = min(n - 1, e // 10)         # last block whose start <= e
        touched = max(0, hi - lo + 1)
        C.cmps = 0
        got = insert(blocks, (C(s), C(e)))
        used = C.cmps
        merged = (min(s, 10 * lo), max(e, 10 * hi + 5)) if touched else (s, e)
        assert len(got) == n - touched + 1, (s, e)
        assert (got[lo][0].v, got[lo][1].v) == merged, (s, e)
        for k in [0, lo - 1, lo + 1, len(got) - 1] + [rng.randrange(len(got)) for _ in range(20)]:
            if 0 <= k < len(got) and k != lo:
                i = k if k < lo else k + touched - 1
                assert (got[k][0].v, got[k][1].v) == (10 * i, 10 * i + 5), (s, e, k)
        budget = 3 * math.log2(n) + 3 * touched + 12
        assert used <= budget, f"{used:,} comparisons to insert ({s}, {e}) into {n:,} blocks touching {touched} (budget {budget:.0f}): binary search for the first block it can touch"


# 3. intersect
def test_intersect_examples():
    assert intersect([(0, 2), (5, 10)], [(1, 5), (8, 12)]) == [(1, 2), (8, 10)]
    assert intersect([], [(1, 2)]) == []
    assert intersect([(1, 2)], []) == []
    assert intersect([(1, 3)], [(3, 5)]) == [], "touching is not overlapping"
    assert intersect([(0, 10)], [(1, 2), (4, 5), (7, 8)]) == [(1, 2), (4, 5), (7, 8)]
    assert intersect([(1, 2), (4, 5), (7, 8)], [(0, 10)]) == [(1, 2), (4, 5), (7, 8)]
    assert intersect([(0, 5)], [(0, 5)]) == [(0, 5)]


def test_intersect_random():
    rng = random.Random(5)
    for _ in range(400):
        a = blocks_of(cells(random_intervals(rng, rng.randint(0, 8))))
        b = blocks_of(cells(random_intervals(rng, rng.randint(0, 8))))
        assert intersect(a, b) == blocks_of(cells(a) & cells(b)), (a, b)


def test_intersect_comparisons():
    rng = random.Random(6)
    def blocks(n):
        out, t = [], 0
        for _ in range(n):
            t += rng.randint(1, 20)
            s = t
            t += rng.randint(1, 30)
            out.append((s, t))
        return out
    m = n = 1000
    a, b = blocks(m), blocks(n)
    want = blocks_of(cells(a) & cells(b))
    C.cmps = 0
    got = unwrap(intersect(wrap(a), wrap(b)))
    assert got == want
    budget = 6 * (m + n)
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for two lists of {m:,} blocks (budget {budget:,}): move one pointer per step"
